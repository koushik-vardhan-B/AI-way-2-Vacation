from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List
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
        
        # Generate plan using AI
        react_app = graph_builder()
        messages = {"messages": [full_query]}
        output = react_app.invoke(messages)
        
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
            region=None  # Could extract from query
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
    
    logger.info(f"Plan deleted: ID={plan_id}, User={current_user.username}")
    return None

@router.get("/search/{search_term}", response_model=List[schemas.TravelPlanListResponse])
async def search_my_plans(
    search_term: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_active_user)
):
    """Search your travel plans by destination or title"""
    plans = crud.search_travel_plans(
        db, 
        user_id=current_user.id, 
        search_term=search_term, 
        limit=limit
    )
    return plans
