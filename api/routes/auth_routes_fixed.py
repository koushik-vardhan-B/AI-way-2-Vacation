from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
import logging
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from database import crud, schemas
from database.base import get_db
from api.auth import create_access_token, get_current_active_user, settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["🔐 Authentication"]
)

# Password reset tokens storage (in production, use Redis or database)
password_reset_tokens = {}

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user account"""
    try:
        # Check if email already exists
        db_user = crud.get_user_by_email(db, email=user.email)
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username already exists
        db_user = crud.get_user_by_username(db, username=user.username)
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create new user
        new_user = crud.create_user(db=db, user=user)
        return new_user
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/google-auth", response_model=schemas.TokenWithUser)
async def google_auth(
    google_data: schemas.GoogleAuth,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth authentication"""
    try:
        # Check if user already exists
        user = crud.get_user_by_email(db, email=google_data.email)
        
        if user:
            # User exists, check if it's a Google user
            if user.hashed_password != "google_oauth":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered with regular account"
                )
        else:
            # Create new Google user
            user_data = schemas.UserCreate(
                email=google_data.email,
                username=google_data.username,
                password=secrets.token_urlsafe(32)  # Random password for Google users
            )
            user = crud.create_google_user(
                db=db, 
                user=user_data, 
            )
        
        # Update last login
        crud.update_last_login(db, user.id)
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "username": user.username,
            "email": user.email,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google auth failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google authentication failed"
        )

@router.post("/login", response_model=schemas.TokenWithUser)
async def login(
    user_data: schemas.UserLogin,
    db: Session = Depends(get_db)
):
    """Login with email and password to get access token"""
    try:
        # Find user by email
        user = crud.get_user_by_email(db, email=user_data.email)
        
        if not user or not crud.verify_password(user_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account"
            )
        
        # Update last login
        crud.update_last_login(db, user.id)
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "username": user.username,
            "email": user.email,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login with username and password to get access token (OAuth2 compatible)"""
    try:
        # FIX: Use email lookup since OAuth2PasswordRequestForm uses 'username' field for email
        user = crud.get_user_by_email(db, email=form_data.username)
        
        if not user or not crud.verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account"
            )
        
        # Update last login
        crud.update_last_login(db, user.id)
        
        # Create access token with username as subject (this is correct)
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username},  # ✅ This is correct
            expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/forgot-password")
async def forgot_password(
    email_data: schemas.ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Send password reset email ONLY if user exists"""
    try:
        user = crud.get_user_by_email(db, email=email_data.email)
        
        # Only send email if user exists
        if not user:
            logger.warning(f"Password reset attempted for non-existent email: {email_data.email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found with this email address"
            )
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        password_reset_tokens[reset_token] = {
            "email": user.email,
            "expires": datetime.utcnow() + timedelta(hours=24)
        }
        
        # Send email in background
        background_tasks.add_task(send_password_reset_email, user.email, reset_token)
        
       
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forgot password failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process reset request"
        )

def send_password_reset_email(email: str, token: str):
    """Send password reset email and track success"""
    try:
        # Email configuration
        smtp_server = settings.SMTP_SERVER
        smtp_port = settings.SMTP_PORT
        smtp_username = settings.SMTP_USERNAME
        smtp_password = settings.SMTP_PASSWORD
        from_email = settings.FROM_EMAIL
        
        # Create reset link
        reset_link = f"{settings.FRONTEND_URL}/reset-password/{token}"
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = email
        msg['Subject'] = "AI Trip Planner - Password Reset Request"
        
        # Email body
        body = f"""
        <html>
        <body>
            <h2>AI Trip Planner - Password Reset</h2>
            <p>You have requested to reset your password.</p>
            <p>Click the link below to reset your password:</p>
            <a href="{reset_link}" style="
                background-color: #007bff;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 5px;
                display: inline-block;
            ">Reset Password</a>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't request this reset, please ignore this email.</p>
            <br>
            <p>Best regards,<br>AI Trip Planner Team</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        # Mark as sent successfully
        password_reset_tokens[token]["sent"] = True
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {email}: {e}")
        # Optionally remove the token if email failed
        if token in password_reset_tokens:
            del password_reset_tokens[token]

@router.post("/reset-password")
async def reset_password(
    reset_data: schemas.ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Reset user password with token"""
    try:
        # Verify token
        token_data = password_reset_tokens.get(reset_data.token)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Check token expiration
        if datetime.utcnow() > token_data["expires"]:
            del password_reset_tokens[reset_data.token]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expired reset token"
            )
        
        # Get email from token data
        user_email = token_data["email"]
        
        # Find user by email from token
        user = crud.get_user_by_email(db, email=user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )
        
        # Update password
        user_update = schemas.UserUpdate(password=reset_data.new_password)
        updated_user = crud.update_user(db, user.id, user_update)
        
        # Remove used token
        del password_reset_tokens[reset_data.token]
        
        return {"message": "Password reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )

@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: schemas.UserResponse = Depends(get_current_active_user)
):
    """Get current logged-in user information"""
    return current_user

