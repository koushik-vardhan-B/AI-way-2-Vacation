from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List
import logging
import time
import json

from database import crud, schemas
from database.base import get_db
from api.auth import get_current_active_user
from agent.agentic_workflow import GraphBuilder
from api.dependencies import get_graph_builder
from utils.save_to_document import save_document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plans", tags=["📋 Travel Plans"])

# Store conversation histories per plan (in production, use Redis or database)
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
    """
    start_time = time.time()
    
    try:
        # Build AI query
        query_parts = [f"Plan a {request.duration}-day trip to {request.destination}"]
        if request.budget:
            query_parts.append(f"with a budget of {request.currency} {request.budget}")
        if request.preferences:
            query_parts.append(f"focusing on {', '.join(request.preferences)} activities")
        if request.group_size > 1:
            query_parts.append(f"for {request.group_size} people")
        
        full_query = " ".join(query_parts)
        logger.info(f"Generating plan for user {current_user.username}: {full_query}")
        
        # Generate plan using AI with unique thread_id for this plan
        react_app = graph_builder()
        thread_id = f"user_{current_user.id}_new_plan"
        
        config = {"configurable": {"thread_id": thread_id}}
        messages = {"messages": [full_query]}
        output = react_app.invoke(messages, config)
        
        # Extract content
        if isinstance(output, dict) and "messages" in output:
            plan_content = output["messages"][-1].content
        else:
            plan_content = str(output)
        
        execution_time = time.time() - start_time
        
        # Create plan in database
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
        
        # Store conversation history for this plan
        conversation_store[db_plan.id] = [
            {"role": "user", "content": full_query},
            {"role": "assistant", "content": plan_content}
        ]
        
        # Log query
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
        
        logger.info(f"Plan created successfully: ID={db_plan.id}, User={current_user.username}")
        
        return db_plan
        
    except Exception as e:
        logger.error(f"Error generating plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate travel plan: {str(e)}"
        )


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
    
    This endpoint allows you to:
    - Ask questions about your plan
    - Request modifications
    - Get additional recommendations
    """
    try:
        # Verify plan belongs to user
        plan = crud.get_travel_plan(db, plan_id=plan_id, user_id=current_user.id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Travel plan not found"
            )
        
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
        
        output = react_app.invoke({"messages": langgraph_messages}, config)
        
        # Extract response
        if isinstance(output, dict) and "messages" in output:
            ai_response = output["messages"][-1].content
        else:
            ai_response = str(output)
        
        # Update conversation history
        conversation_history.append({"role": "assistant", "content": ai_response})
        conversation_store[plan_id] = conversation_history
        
        # Update plan content with latest information
        updated_content = f"{plan.content}\n\n---\n\n**User:** {message}\n\n**Assistant:** {ai_response}"
        
        plan_update = schemas.TravelPlanUpdate(content=updated_content)
        updated_plan = crud.update_travel_plan(
            db,
            plan_id=plan_id,
            user_id=current_user.id,
            plan_update=plan_update
        )
        
        logger.info(f"Conversation continued for plan {plan_id}")
        
        return updated_plan
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in conversation: {e}")
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
    """Get conversation history for a plan"""
    # Verify plan belongs to user
    plan = crud.get_travel_plan(db, plan_id=plan_id, user_id=current_user.id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel plan not found"
        )
    
    # Return conversation history
    history = conversation_store.get(plan_id, [])
    return {
        "plan_id": plan_id,
        "conversation": history,
        "message_count": len(history)
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
    """Delete travel plan"""
    success = crud.delete_travel_plan(db, plan_id=plan_id, user_id=current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel plan not found"
        )
    
    # Clear conversation history
    if plan_id in conversation_store:
        del conversation_store[plan_id]
    
    logger.info(f"Plan deleted: ID={plan_id}, User={current_user.username}")
    return None
# @router.get("/search/{search_term}", response_model=List[schemas.TravelPlanListResponse])
# async def search_my_plans(
#     search_term: str,
#     limit: int = 10,
#     db: Session = Depends(get_db),
#     current_user: schemas.UserResponse = Depends(get_current_active_user)
# ):
#     """Search your travel plans by destination or title"""
#     plans = crud.search_travel_plans(
#         db, 
#         user_id=current_user.id, 
#         search_term=search_term, 
#         limit=limit
#     )
#     return plans
