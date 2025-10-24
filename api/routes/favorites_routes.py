from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from database import crud, schemas
from database.base import get_db
from api.auth import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/favorites", tags=["⭐ Favorites"])

@router.post("/", response_model=schemas.FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    favorite: schemas.FavoriteCreate,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_active_user)
):
    """Add destination to favorites"""
    db_favorite = crud.create_favorite(db=db, favorite=favorite, user_id=current_user.id)
    logger.info(f"Favorite added: {favorite.destination_name} by {current_user.username}")
    return db_favorite

@router.get("/", response_model=List[schemas.FavoriteResponse])
async def get_my_favorites(
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_active_user)
):
    """Get all favorite destinations"""
    favorites = crud.get_user_favorites(db, user_id=current_user.id)
    return favorites

@router.delete("/{favorite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    favorite_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_active_user)
):
    """Remove destination from favorites"""
    success = crud.delete_favorite(db, favorite_id=favorite_id, user_id=current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )
    
    logger.info(f"Favorite deleted: ID={favorite_id}, User={current_user.username}")
    return None

# @router.delete("/by-name/{destination_name}", status_code=status.HTTP_204_NO_CONTENT)
# async def remove_favorite_by_name(
#     destination_name: str,
#     db: Session = Depends(get_db),
#     current_user: schemas.UserResponse = Depends(get_current_active_user)
# ):
#     """Remove favorite by destination name"""
#     success = crud.delete_favorite_by_name(
#         db, 
#         destination_name=destination_name, 
#         user_id=current_user.id
#     )
    
#     if not success:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Favorite not found"
#         )
    
#     return None
