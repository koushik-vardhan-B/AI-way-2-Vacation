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
# CONVERSATION PERSISTENCE: Now stored in database!
# Conversations are persisted in the travel_plans table
# ============================================================================
# In your plans_routes.py - Update the continue_conversation function

@router.post("/chat/{plan_id}", response_model=schemas.ChatResponse)
async def continue_conversation(
    plan_id: int,
    request: schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_active_user),
    graph_builder: GraphBuilder = Depends(get_graph_builder)
):
    """
    Continue conversation about an existing travel plan and SAVE to database
    """
    try:
        message = request.message
        
        # Verify plan belongs to user
        plan = crud.get_travel_plan(db, plan_id=plan_id, user_id=current_user.id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Travel plan not found"
            )
        
        # Load conversation history from database
        conversation_history = plan.conversation_history or []
        
        # If no conversation history exists, initialize with the original plan content
        if not conversation_history:
            conversation_history = [
                {"role": "assistant", "content": plan.content}
            ]
        
        # Add user message to conversation history
        conversation_history.append({"role": "user", "content": message})
        
        # Convert to LangChain message format
        langgraph_messages = []
        for msg in conversation_history:
            if msg["role"] == "user":
                langgraph_messages.append(HumanMessage(content=msg["content"]))
            else:
                langgraph_messages.append(AIMessage(content=msg["content"]))
        
        # Generate response with full context
        react_app = graph_builder()
        
        # Use existing thread_id or create new one
        thread_id = plan.thread_id or f"user_{current_user.id}_plan_{plan_id}"
        config = {"configurable": {"thread_id": thread_id}}
        
        # Generate AI response
        max_retries = 2
        ai_response = ""
        
        for attempt in range(max_retries):
            try:
                output = react_app.invoke({"messages": langgraph_messages}, config)
                
                # Extract response
                if isinstance(output, dict) and "messages" in output:
                    last_message = output["messages"][-1]
                    ai_response = last_message.content if hasattr(last_message, 'content') else str(last_message)
                else:
                    ai_response = str(output)
                break  # Success, exit retry loop
                
            except Exception as invoke_error:
                if "tool_use_failed" in str(invoke_error) or "Failed to call a function" in str(invoke_error):
                    if attempt < max_retries - 1:
                        # Simplify the last user message to avoid tool calling issues
                        if langgraph_messages and isinstance(langgraph_messages[-1], HumanMessage):
                            simplified_msg = HumanMessage(
                                content=f"Please provide information about: {langgraph_messages[-1].content}"
                            )
                            langgraph_messages[-1] = simplified_msg
                        continue
                    else:
                        # Last attempt failed, provide fallback response
                        ai_response = f"I apologize, but I'm having trouble processing your request about {plan.destination}. Please try rephrasing your question or ask something more specific about your trip plan."
                        break
                else:
                    # Non-tool-calling error, re-raise
                    raise
        
        # CRITICAL FIX: Create a NEW list to avoid reference issues
        updated_conversation_history = conversation_history.copy()
        updated_conversation_history.append({"role": "assistant", "content": ai_response})
        
        # Save updated conversation to database for persistence
        updated_plan = crud.update_conversation_history(
            db=db,
            plan_id=plan_id,
            user_id=current_user.id,
            conversation_history=updated_conversation_history,  # Use the NEW list
            thread_id=thread_id
        )
        
        if not updated_plan:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save conversation to database"
            )
        
        return schemas.ChatResponse(
            message=ai_response,
            conversation_history=updated_conversation_history,
            plan_id=plan_id,
            thread_id=thread_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )
        
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
        # CONVERSATION MEMORY: Store in database for persistence
        # This ensures conversations survive server restarts
        # ================================================================
        initial_conversation = [
            {"role": "user", "content": full_query},
            {"role": "assistant", "content": plan_content}
        ]
        crud.update_conversation_history(
            db=db,
            plan_id=db_plan.id,
            user_id=current_user.id,
            conversation_history=initial_conversation,
            thread_id=thread_id
        )
        
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
        


        return db_plan
        
    except Exception as e:
        logger.error(f"Error generating plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate travel plan: {str(e)}"
        )

# Replace the continue_conversation function in api/routes/plans_routes.py

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
    """
    Get specific travel plan by ID with full conversation history
    
    This endpoint returns the complete plan including:
    - Plan details (destination, duration, budget, etc.)
    - Full content/itinerary
    - Complete conversation history (all chat messages)
    - Thread ID for continued conversations
    """
    plan = crud.get_travel_plan(db, plan_id=plan_id, user_id=current_user.id)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel plan not found"
        )
    
    # Log what we're returning to help debug frontend issues
    conv_count = len(plan.conversation_history) if plan.conversation_history else 0
    
    if conv_count == 0:
        logger.warning(f"⚠️  Plan {plan_id} has NO conversation history - this may cause issues on frontend")
    
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
    
    # Return conversation history from database
    conversation_history = plan.conversation_history or []
    
    return {
        "plan_id": plan_id,
        "thread_id": plan.thread_id or "",
        "conversation": conversation_history,
        "message_count": len(conversation_history)
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
    
    # Conversation history is automatically deleted with the plan (cascade)
    return None