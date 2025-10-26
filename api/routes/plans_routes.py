from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List
from langchain_core.messages import HumanMessage, AIMessage
import logging
import time

from database import crud, schemas
from database.base import get_db
from api.auth import get_current_active_user
from agent.agentic_workflow import GraphBuilder
from api.dependencies import get_graph_builder
from utils.save_to_document import save_document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plans", tags=["📋 Travel Plans"])

# ============================================================================
# IMPORTANT: In-memory conversation store
# In production, replace this with Redis or database storage
# ============================================================================
conversation_store = {}

@router.post("/generate", response_model=schemas.TravelPlanResponse, status_code=status.HTTP_201_CREATED)
async def generate_and_save_travel_plan(
    request: schemas.TravelPlanBase,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_active_user),
    graph_builder: GraphBuilder = Depends(get_graph_builder)
):
    """
    Generate a new AI travel plan and save it to database
    
    This endpoint:
    1. Uses AI to generate comprehensive travel itinerary
    2. Saves the plan to your account
    3. Returns the complete plan with ID
    4. Initializes conversation memory for this plan
    """
    start_time = time.time()
    
    try:
        # Build AI query from request parameters
        query_parts = [f"Plan a {request.duration}-day trip to {request.destination}"]
        if request.budget:
            query_parts.append(f"with a budget of {request.currency} {request.budget}")
        if request.preferences:
            query_parts.append(f"focusing on {', '.join(request.preferences)} activities")
        if request.group_size > 1:
            query_parts.append(f"for {request.group_size} people")
        
        full_query = " ".join(query_parts)
        logger.info(f"Generating plan for user {current_user.username}: {full_query}")
        
        # ================================================================
        # MEMORY SETUP: Create unique thread_id for this conversation
        # This thread_id will be used to track all messages for this plan
        # ================================================================
        thread_id = f"user_{current_user.id}_new_plan_{int(time.time())}"
        config = {"configurable": {"thread_id": thread_id}}
        
        # Build the graph and invoke with memory
        react_app = graph_builder()
        messages = {"messages": [HumanMessage(content=full_query)]}
        
        # Invoke with config containing thread_id
        # LangGraph will automatically store this conversation in memory
        output = react_app.invoke(messages, config)
        
        # Extract AI response
        if isinstance(output, dict) and "messages" in output:
            plan_content = output["messages"][-1].content
        else:
            plan_content = str(output)
        
        execution_time = time.time() - start_time
        
        # ================================================================
        # DATABASE: Save the plan
        # ================================================================
        plan_data = schemas.TravelPlanCreate(
            title=f"{request.duration}-Day Trip to {request.destination}",
            destination=request.destination,
            duration=request.duration,
            budget=request.budget,
            currency=request.currency,
            preferences=request.preferences,
            group_size=request.group_size,
            content=plan_content,
            summary=plan_content[:500] if len(plan_content) > 500 else plan_content
        )
        
        db_plan = crud.create_travel_plan(db=db, plan=plan_data, user_id=current_user.id)
        
        # ================================================================
        # CONVERSATION MEMORY: Store thread_id for this plan
        # This links the plan_id to its conversation thread
        # ================================================================
        conversation_store[db_plan.id] = {
            "thread_id": thread_id,
            "messages": [
                {"role": "user", "content": full_query},
                {"role": "assistant", "content": plan_content}
            ]
        }
        
        # Log query for analytics
        query_log = schemas.QueryCreate(
            query_text=full_query,
            response_length=len(plan_content),
            status_code=201,
            execution_time=execution_time
        )
        crud.create_query(db=db, query=query_log, user_id=current_user.id)
        
        # Update destination popularity
        crud.get_or_create_destination(
            db=db,
            name=request.destination,
            region=None
        )
        
        # Save to file in background
        background_tasks.add_task(save_document, plan_content)
        
        logger.info(f"Plan created: ID={db_plan.id}, Thread={thread_id}")
        
        return db_plan
        
    except Exception as e:
        logger.error(f"Error generating plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate travel plan: {str(e)}"
        )

# Replace the continue_conversation function in api/routes/plans_routes.py

@router.post("/chat/{plan_id}", response_model=schemas.TravelPlanResponse)
async def continue_conversation(
    plan_id: int,
    message: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_active_user),
    graph_builder: GraphBuilder = Depends(get_graph_builder)
):
    """
    Continue conversation about an existing travel plan
    """
    try:
        # Verify plan belongs to user
        plan = crud.get_travel_plan(db, plan_id=plan_id, user_id=current_user.id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Travel plan not found"
            )
        
        logger.info(f"💬 Chat request for plan {plan_id}: {message[:100]}...")
        
        # Get or initialize conversation history
        if plan_id not in conversation_store:
            conversation_store[plan_id] = [
                {"role": "assistant", "content": plan.content}
            ]
        
        # Build conversation context
        conversation_history = conversation_store[plan_id]
        
        # Add user message
        conversation_history.append({"role": "user", "content": message})
        
        # Convert to LangChain message format
        from langchain_core.messages import HumanMessage, AIMessage
        langgraph_messages = []
        for msg in conversation_history:
            if msg["role"] == "user":
                langgraph_messages.append(HumanMessage(content=msg["content"]))
            else:
                langgraph_messages.append(AIMessage(content=msg["content"]))
        
        # Generate response with full context
        react_app = graph_builder()
        thread_id = f"user_{current_user.id}_plan_{plan_id}"
        config = {"configurable": {"thread_id": thread_id}}
        
        logger.info(f"🤖 Invoking AI agent for plan {plan_id}...")
        output = react_app.invoke({"messages": langgraph_messages}, config)
        
        # Extract response - THIS IS THE KEY FIX
        ai_response = ""
        if isinstance(output, dict) and "messages" in output:
            last_message = output["messages"][-1]
            ai_response = last_message.content if hasattr(last_message, 'content') else str(last_message)
        else:
            ai_response = str(output)
        
        logger.info(f"✅ AI response generated ({len(ai_response)} chars): {ai_response[:200]}...")
        
        # Update conversation history
        conversation_history.append({"role": "assistant", "content": ai_response})
        conversation_store[plan_id] = conversation_history
        
        # DON'T update the database content yet - just return the AI response
        # The full content update should happen only on explicit save
        
        logger.info(f"💾 Conversation for plan {plan_id} updated (messages: {len(conversation_history)})")
        
        # Create a response object that matches TravelPlanResponse schema
        # but with the AI response as the main content
        response_plan = schemas.TravelPlanResponse(
            id=plan.id,
            user_id=plan.user_id,
            title=plan.title,
            destination=plan.destination,
            duration=plan.duration,
            budget=plan.budget,
            currency=plan.currency,
            content=ai_response,  # THIS IS THE KEY - return the AI response, not the full plan
            summary=plan.summary,
            preferences=plan.preferences,
            group_size=plan.group_size,
            status=plan.status,
            created_at=plan.created_at,
            updated_at=plan.updated_at
        )
        
        logger.info(f"📤 Sending response for plan {plan_id}")
        
        return response_plan
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in conversation for plan {plan_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get("/", response_model=List[schemas.TravelPlanListResponse])
async def get_my_travel_plans(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_active_user)
):
    """Get all travel plans for current user"""
    plans = crud.get_travel_plans(db, user_id=current_user.id, skip=skip, limit=limit)
    return plans


@router.get("/{plan_id}", response_model=schemas.TravelPlanResponse)
async def get_travel_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_active_user)
):
    """Get specific travel plan by ID"""
    plan = crud.get_travel_plan(db, plan_id=plan_id, user_id=current_user.id)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel plan not found"
        )
    
    return plan


@router.get("/{plan_id}/history")
async def get_conversation_history(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_active_user)
):
    """
    Get full conversation history for a plan
    
    Returns all messages exchanged about this plan
    """
    # Verify plan belongs to user
    plan = crud.get_travel_plan(db, plan_id=plan_id, user_id=current_user.id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel plan not found"
        )
    
    # Return conversation history
    conversation_data = conversation_store.get(plan_id, {})
    messages = conversation_data.get("messages", [])
    
    return {
        "plan_id": plan_id,
        "thread_id": conversation_data.get("thread_id", ""),
        "conversation": messages,
        "message_count": len(messages)
    }


@router.put("/{plan_id}", response_model=schemas.TravelPlanResponse)
async def update_travel_plan(
    plan_id: int,
    plan_update: schemas.TravelPlanUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_active_user)
):
    """Update travel plan"""
    updated_plan = crud.update_travel_plan(
        db, 
        plan_id=plan_id, 
        user_id=current_user.id, 
        plan_update=plan_update
    )
    
    if not updated_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel plan not found"
        )
    
    logger.info(f"Plan updated: ID={plan_id}, User={current_user.username}")
    return updated_plan


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_travel_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_active_user)
):
    """Delete travel plan and its conversation memory"""
    success = crud.delete_travel_plan(db, plan_id=plan_id, user_id=current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel plan not found"
        )
    
    # Clear conversation memory for this plan
    if plan_id in conversation_store:
        del conversation_store[plan_id]
        logger.info(f"Cleared conversation memory for plan {plan_id}")
    
    logger.info(f"Plan deleted: ID={plan_id}, User={current_user.username}")
    return None