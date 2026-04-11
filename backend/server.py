from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, APIRouter, HTTPException, Request, File, UploadFile, Depends, Header, Query, Response
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import time
import asyncio
import cloudinary
import cloudinary.uploader
import cloudinary.utils
import resend
import base64
import httpx
from bson import ObjectId
import razorpay
import hmac
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent

# MongoDB connection
import certifi
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url, tlsCAFile=certifi.where())
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_ALGORITHM = "HS256"
JWT_SECRET = os.environ.get('JWT_SECRET')

# Cloudinary Configuration
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)

# Resend Configuration
resend.api_key = os.environ.get("RESEND_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "noreply@matchme.app")

# Anthropic Configuration (for photo moderation)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Razorpay Configuration
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
razorpay_client = None
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# ==================== PHOTO MODERATION ====================
async def moderate_photo(image_data: bytes, content_type: str) -> dict:
    """
    Use Claude vision to check if a photo is safe for the platform.
    Returns {"safe": bool, "reason": str}
    """
    if not ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not set — skipping moderation")
        return {"safe": True, "reason": "moderation_skipped"}

    try:
        media_type = content_type if content_type in ["image/jpeg", "image/png", "image/gif", "image/webp"] else "image/jpeg"
        image_b64 = base64.standard_b64encode(image_data).decode("utf-8")

        payload = {
            "model": "claude-opus-4-5",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_b64
                            }
                        },
                        {
                            "type": "text",
                            "text": (
                                "You are a content moderator for a dating profile review app. "
                                "Analyze this photo and respond with ONLY a JSON object like: "
                                "{\"safe\": true} or {\"safe\": false, \"reason\": \"brief reason\"}. "
                                "Flag as unsafe ONLY if the image contains: explicit nudity or sexual content, "
                                "graphic violence or gore, or content that is clearly not a person/profile photo "
                                "(e.g. genitalia, explicit acts). "
                                "Normal swimwear, shirtless photos, and tasteful images are SAFE. "
                                "Do not flag based on attractiveness, age appearance, or race. "
                                "Respond with only the JSON, nothing else."
                            )
                        }
                    ]
                }
            ]
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json=payload
            )
            resp.raise_for_status()
            result = resp.json()

        text = result["content"][0]["text"].strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        import json as _json
        moderation = _json.loads(text)
        logger.info(f"Moderation result: {moderation}")
        return moderation

    except Exception as e:
        logger.error(f"Moderation error: {e}")
        # Fail open — don't block uploads if moderation is down
        return {"safe": True, "reason": "moderation_error"}

# ==================== TIER CONFIGURATION ====================
TIER_CONFIG = {
    "free": {
        "min_ratings": 3,
        "time_cap_hours": 24,
        "low_confidence_min": 2,
        "extension_hours": 12,
        "credits_per_month": None,  # Not subscription-based
        "signup_credits": 3,
        "ratings_for_credit": 5,
        "max_daily_earned_credits": 5,
    },
    "priority": {
        "min_ratings": 7,
        "time_cap_hours": 4,
        "low_confidence_min": 4,
        "extension_hours": 2,
        "credits_per_month": 12,
        "price_monthly": 9.00,
    },
    "pro": {
        "min_ratings": 10,
        "time_cap_hours": 4,
        "low_confidence_min": 6,
        "extension_hours": 2,
        "credits_per_month": None,  # Unlimited - no credit system
        "price_monthly": 25.00,
        "unlimited": True,
    }
}

# Credit costs
BEST_SHOT_COST = 1
PROFILE_ANALYSIS_COST = 2

# Create the main app
app = FastAPI(title="MatchMe API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ==================== PASSWORD HASHING ====================
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

# ==================== JWT TOKEN MANAGEMENT ====================
def get_jwt_secret() -> str:
    return os.environ["JWT_SECRET"]

def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "type": "access"
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "refresh"
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

# ==================== AUTH HELPER ====================
async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"user_id": payload["sub"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_optional_user(request: Request) -> Optional[dict]:
    try:
        return await get_current_user(request)
    except HTTPException:
        return None

# ==================== EMAIL SERVICE (RESEND) ====================
async def send_email(to_email: str, subject: str, html_content: str):
    """Send email using Resend API"""
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        email = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Email sent to {to_email}: {email.get('id')}")
        return email
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return None

async def send_results_email(user_email: str, user_name: str, job_type: str, job_id: str, rater_count: int, low_confidence: bool = False):
    """Send notification when job is complete"""
    frontend_url = os.environ.get("FRONTEND_URL", "https://matchme-preview.preview.emergentagent.com")
    results_url = f"{frontend_url}/results/{job_id}"
    
    subject = f"[{rater_count}] people reviewed your photos — see results"
    
    confidence_note = ""
    if low_confidence:
        confidence_note = """
        <p style="background: #FFF3CD; padding: 12px; border-radius: 8px; font-size: 14px;">
            <strong>Note:</strong> Your results are based on fewer reviews than usual. 
            Consider submitting again for more comprehensive feedback.
        </p>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #1A1A1A; }}
            .container {{ max-width: 500px; margin: 0 auto; padding: 40px 20px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .header h1 {{ font-family: Georgia, serif; font-size: 28px; margin: 0; }}
            .content {{ background: #F7F7F5; border-radius: 16px; padding: 30px; margin-bottom: 30px; }}
            .btn {{ display: inline-block; background: #1A1A1A; color: white; padding: 16px 32px; border-radius: 50px; text-decoration: none; font-weight: 500; }}
            .footer {{ text-align: center; color: #666666; font-size: 14px; }}
            .stat {{ font-size: 48px; font-weight: bold; color: #C9B8E8; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>MatchMe</h1>
            </div>
            <div class="content">
                <p>Hi {user_name},</p>
                <p style="text-align: center;">
                    <span class="stat">{rater_count}</span><br>
                    <span>people reviewed your photos</span>
                </p>
                <p>Your <strong>{job_type.replace('-', ' ')}</strong> results are ready! We've analyzed the feedback to help you get more matches.</p>
                {confidence_note}
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{results_url}" class="btn">View Your Results</a>
                </p>
            </div>
            <div class="footer">
                <p>© 2026 MatchMe. Get more matches.</p>
            </div>
        </div>
    </body>
    </html>
    """
    await send_email(user_email, subject, html_content)

async def send_job_failed_email(user_email: str, user_name: str, job_type: str, refunded: bool = False, refund_amount: int = 0):
    """Send apology email when job fails due to insufficient ratings"""
    frontend_url = os.environ.get("FRONTEND_URL", "https://matchme-preview.preview.emergentagent.com")
    
    subject = "We couldn't complete your photo review"
    
    refund_note = ""
    if refunded:
        refund_note = f"""
        <p style="background: #D4EDDA; padding: 12px; border-radius: 8px; font-size: 14px;">
            <strong>Good news:</strong> We've refunded {refund_amount} credit(s) to your account.
        </p>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #1A1A1A; }}
            .container {{ max-width: 500px; margin: 0 auto; padding: 40px 20px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .header h1 {{ font-family: Georgia, serif; font-size: 28px; margin: 0; }}
            .content {{ background: #F7F7F5; border-radius: 16px; padding: 30px; margin-bottom: 30px; }}
            .btn {{ display: inline-block; background: #1A1A1A; color: white; padding: 16px 32px; border-radius: 50px; text-decoration: none; font-weight: 500; }}
            .footer {{ text-align: center; color: #666666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>MatchMe</h1>
            </div>
            <div class="content">
                <p>Hi {user_name},</p>
                <p>We're sorry, but we weren't able to gather enough reviews for your <strong>{job_type.replace('-', ' ')}</strong> submission.</p>
                <p>This can happen during periods of lower activity. We recommend trying again — most submissions get reviewed quickly!</p>
                {refund_note}
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{frontend_url}/dashboard" class="btn">Try Again</a>
                </p>
            </div>
            <div class="footer">
                <p>© 2026 MatchMe. Get more matches.</p>
            </div>
        </div>
    </body>
    </html>
    """
    await send_email(user_email, subject, html_content)

# ==================== PYDANTIC MODELS ====================
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class OnboardingData(BaseModel):
    gender: str
    orientation: str
    dating_app: str

class JobCreate(BaseModel):
    photo_ids: List[str]
    bio: Optional[str] = None
    prompt_answer: Optional[str] = None

class RatingSubmit(BaseModel):
    photo_id: str
    confident: int = Field(ge=1, le=5)
    approachable: int = Field(ge=1, le=5)
    attractive: int = Field(ge=1, le=5)
    tags: List[str] = []
    comment: str

class CheckoutRequest(BaseModel):
    package_id: str

class RazorpayVerifyRequest(BaseModel):
    razorpay_payment_id: str
    razorpay_subscription_id: str
    razorpay_signature: str
    package_id: str

# ==================== AUTH ROUTES ====================
@api_router.post("/auth/register")
async def register(data: UserRegister, response: Response):
    email = data.email.lower()
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user_doc = {
        "user_id": user_id,
        "email": email,
        "name": data.name,
        "password_hash": hash_password(data.password),
        "credits": TIER_CONFIG["free"]["signup_credits"],  # 3 credits on signup
        "gender": None,
        "orientation": None,
        "dating_app": None,
        "tier": "free",
        "stripe_customer_id": None,
        "stripe_subscription_id": None,
        "razorpay_subscription_id": None,
        "razorpay_payment_id": None,
        "subscription_start_date": None,
        "ratings_given": 0,
        "ratings_earned": 0,
        "ratings_since_last_credit": 0,
        "job_bonus_count": 0,
        "onboarding_completed": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="none", max_age=900, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="none", max_age=604800, path="/")
    
    return {
        "user_id": user_id,
        "email": email,
        "name": data.name,
        "credits": TIER_CONFIG["free"]["signup_credits"],
        "tier": "free",
        "onboarding_completed": False
    }

@api_router.post("/auth/login")
async def login(data: UserLogin, response: Response, request: Request):
    email = data.email.lower()
    identifier = f"{request.client.host}:{email}"
    
    # Check brute force
    attempt = await db.login_attempts.find_one({"identifier": identifier}, {"_id": 0})
    if attempt and attempt.get("count", 0) >= 5:
        lockout_time = datetime.fromisoformat(attempt["last_attempt"])
        if lockout_time.tzinfo is None:
            lockout_time = lockout_time.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - lockout_time < timedelta(minutes=15):
            raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")
    
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user or not verify_password(data.password, user.get("password_hash", "")):
        await db.login_attempts.update_one(
            {"identifier": identifier},
            {"$inc": {"count": 1}, "$set": {"last_attempt": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    await db.login_attempts.delete_one({"identifier": identifier})
    
    access_token = create_access_token(user["user_id"], email)
    refresh_token = create_refresh_token(user["user_id"])
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="none", max_age=900, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="none", max_age=604800, path="/")
    
    user.pop("password_hash", None)
    return user

@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    return {"message": "Logged out successfully"}

@api_router.get("/auth/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    return user

@api_router.post("/auth/refresh")
async def refresh_token(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"user_id": payload["sub"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        access_token = create_access_token(user["user_id"], user["email"])
        response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="none", max_age=900, path="/")
        return {"message": "Token refreshed"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

# ==================== GOOGLE OAUTH ====================
@api_router.post("/auth/google/session")
async def google_session(request: Request, response: Response):
    body = await request.json()
    session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    import requests
    auth_response = requests.get(
        "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
        headers={"X-Session-ID": session_id},
        timeout=30
    )
    if auth_response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    data = auth_response.json()
    email = data["email"].lower()
    
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user_doc = {
            "user_id": user_id,
            "email": email,
            "name": data.get("name", email.split("@")[0]),
            "google_id": data.get("id"),
            "picture": data.get("picture"),
            "password_hash": None,
            "credits": TIER_CONFIG["free"]["signup_credits"],
            "gender": None,
            "orientation": None,
            "dating_app": None,
            "tier": "free",
            "stripe_customer_id": None,
            "stripe_subscription_id": None,
            "razorpay_subscription_id": None,
            "razorpay_payment_id": None,
            "subscription_start_date": None,
            "ratings_given": 0,
            "ratings_earned": 0,
            "ratings_since_last_credit": 0,
            "job_bonus_count": 0,
            "onboarding_completed": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
        user = user_doc
    else:
        user_id = user["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"google_id": data.get("id"), "picture": data.get("picture")}}
        )
    
    access_token = create_access_token(user["user_id"], email)
    refresh_token = create_refresh_token(user["user_id"])
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="none", max_age=900, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="none", max_age=604800, path="/")
    
    user.pop("password_hash", None)
    user.pop("_id", None)
    return user

# ==================== ONBOARDING ====================
@api_router.post("/user/onboarding")
async def complete_onboarding(data: OnboardingData, request: Request):
    user = await get_current_user(request)
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "gender": data.gender,
            "orientation": data.orientation,
            "dating_app": data.dating_app,
            "onboarding_completed": True
        }}
    )
    return {"message": "Onboarding completed"}

# ==================== CLOUDINARY UPLOAD ====================
@api_router.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    """Direct upload to Cloudinary from backend"""
    user = await get_current_user(request)
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPG/PNG images allowed")
    
    # Read file (max 10MB)
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    # ---- MODERATION CHECK ----
    moderation = await moderate_photo(data, file.content_type)
    if not moderation.get("safe", True):
        reason = moderation.get("reason", "inappropriate content")
        logger.warning(f"Photo blocked by moderation for user {user['user_id']}: {reason}")
        raise HTTPException(
            status_code=400,
            detail=f"Photo rejected: {reason}. Please upload an appropriate profile photo."
        )

    photo_id = str(uuid.uuid4())
    folder = f"matchme/users/{user['user_id']}/photos"
    
    # Upload to Cloudinary
    try:
        result = await asyncio.to_thread(
            cloudinary.uploader.upload,
            data,
            folder=folder,
            public_id=photo_id,
            resource_type="image"
        )
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload image")
    
    photo_doc = {
        "photo_id": photo_id,
        "user_id": user["user_id"],
        "public_id": result["public_id"],
        "url": result["secure_url"],
        "original_filename": file.filename,
        "content_type": file.content_type,
        "width": result.get("width"),
        "height": result.get("height"),
        "size": result.get("bytes"),
        "is_deleted": False,
        "report_count": 0,
        "moderation_passed": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.photos.insert_one(photo_doc)
    
    return {
        "photo_id": photo_id,
        "url": result["secure_url"],
        "public_id": result["public_id"],
        "created_at": photo_doc["created_at"]
    }

@api_router.delete("/photos/{photo_id}")
async def delete_photo(photo_id: str, request: Request):
    """Delete photo from Cloudinary and database"""
    user = await get_current_user(request)
    
    photo = await db.photos.find_one(
        {"photo_id": photo_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    try:
        await asyncio.to_thread(
            cloudinary.uploader.destroy,
            photo["public_id"],
            invalidate=True
        )
    except Exception as e:
        logger.error(f"Cloudinary delete failed: {e}")
    
    await db.photos.update_one(
        {"photo_id": photo_id},
        {"$set": {"is_deleted": True}}
    )
    
    return {"message": "Photo deleted"}

@api_router.get("/user/photos")
async def get_user_photos(request: Request):
    user = await get_current_user(request)
    photos = await db.photos.find(
        {"user_id": user["user_id"], "is_deleted": False},
        {"_id": 0}
    ).to_list(100)
    return photos

# ==================== JOBS ====================
def check_credits(user: dict, cost: int) -> bool:
    """Check if user has enough credits (Pro users always pass)"""
    if user.get("tier") == "pro":
        return True  # Pro users have no credit system
    return user.get("credits", 0) >= cost

async def deduct_credits(user_id: str, amount: int, tier: str):
    """Deduct credits from user (skip for Pro users)"""
    if tier == "pro":
        return  # Pro users have no credit system
    await db.users.update_one(
        {"user_id": user_id},
        {"$inc": {"credits": -amount}}
    )

@api_router.post("/jobs/best-shot")
async def create_best_shot_job(data: JobCreate, request: Request):
    user = await get_current_user(request)
    
    if len(data.photo_ids) < 3 or len(data.photo_ids) > 10:
        raise HTTPException(status_code=400, detail="Upload 3-10 photos")
    
    if not check_credits(user, BEST_SHOT_COST):
        raise HTTPException(status_code=400, detail="Not enough credits")
    
    job_id = str(uuid.uuid4())
    tier = user.get("tier", "free")
    
    job_doc = {
        "job_id": job_id,
        "user_id": user["user_id"],
        "type": "best-shot",
        "status": "queued",
        "photo_ids": data.photo_ids,
        "tier": tier,
        "result": None,
        "low_confidence": False,
        "extended": False,
        "extension_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None
    }
    await db.jobs.insert_one(job_doc)
    
    # Deduct credit
    await deduct_credits(user["user_id"], BEST_SHOT_COST, tier)
    
    return {"job_id": job_id, "status": "queued", "tier": tier}

@api_router.post("/jobs/profile-analysis")
async def create_profile_analysis_job(data: JobCreate, request: Request):
    user = await get_current_user(request)
    
    if len(data.photo_ids) < 4 or len(data.photo_ids) > 6:
        raise HTTPException(status_code=400, detail="Upload 4-6 photos")
    
    if not check_credits(user, PROFILE_ANALYSIS_COST):
        raise HTTPException(status_code=400, detail="Not enough credits (need 2)")
    
    job_id = str(uuid.uuid4())
    tier = user.get("tier", "free")
    
    job_doc = {
        "job_id": job_id,
        "user_id": user["user_id"],
        "type": "profile-analysis",
        "status": "queued",
        "photo_ids": data.photo_ids,
        "bio": data.bio,
        "prompt_answer": data.prompt_answer,
        "tier": tier,
        "result": None,
        "low_confidence": False,
        "extended": False,
        "extension_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None
    }
    await db.jobs.insert_one(job_doc)
    
    # Deduct credits
    await deduct_credits(user["user_id"], PROFILE_ANALYSIS_COST, tier)
    
    return {"job_id": job_id, "status": "queued", "tier": tier}

@api_router.get("/jobs/{job_id}")
async def get_job(job_id: str, request: Request):
    user = await get_current_user(request)
    job = await db.jobs.find_one({"job_id": job_id, "user_id": user["user_id"]}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@api_router.get("/jobs")
async def get_user_jobs(request: Request):
    user = await get_current_user(request)
    jobs = await db.jobs.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return jobs

# ==================== RATING ====================
@api_router.get("/rate/next")
async def get_next_photo_to_rate(request: Request):
    user = await get_current_user(request)
    
    # Pro users don't earn credits, but can still rate
    tier = user.get("tier", "free")
    
    if tier != "pro":
        # Check daily limit for non-Pro users
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_ratings = await db.ratings.count_documents({
            "rater_id": user["user_id"],
            "created_at": {"$gte": today_start.isoformat()}
        })
        
        max_ratings = TIER_CONFIG["free"]["max_daily_earned_credits"] * TIER_CONFIG["free"]["ratings_for_credit"]
        if today_ratings >= max_ratings:
            raise HTTPException(status_code=400, detail="Daily rating limit reached")
    
    # Find photo to rate (gender matched)
    user_orientation = user.get("orientation", "everyone")
    
    # Find photos from queued jobs that user hasn't rated yet
    rated_photo_ids = await db.ratings.distinct("photo_id", {"rater_id": user["user_id"]})
    reported_photo_ids = await db.reports.distinct("photo_id", {"reporter_id": user["user_id"]})
    
    # Get queued jobs
    pipeline = [
        {"$match": {"status": {"$in": ["queued", "processing"]}}},
        {"$sort": {"created_at": 1}},
        {"$limit": 20}
    ]
    jobs = await db.jobs.aggregate(pipeline).to_list(20)
    
    for job in jobs:
        if job["user_id"] == user["user_id"]:
            continue
        
        # Check gender match
        job_user = await db.users.find_one({"user_id": job["user_id"]}, {"_id": 0})
        if not job_user:
            continue
            
        if user_orientation == "men" and job_user.get("gender") != "man":
            continue
        if user_orientation == "women" and job_user.get("gender") != "woman":
            continue
        
        # Get first unrated, unreported photo from this job
        for photo_id in job.get("photo_ids", []):
            if photo_id not in rated_photo_ids and photo_id not in reported_photo_ids:
                photo = await db.photos.find_one({"photo_id": photo_id, "is_deleted": False}, {"_id": 0})
                if photo:
                    # Count ratings for progress display
                    if tier != "pro":
                        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                        today_ratings = await db.ratings.count_documents({
                            "rater_id": user["user_id"],
                            "created_at": {"$gte": today_start.isoformat()}
                        })
                        progress = today_ratings % TIER_CONFIG["free"]["ratings_for_credit"]
                    else:
                        today_ratings = 0
                        progress = 0
                    
                    return {
                        "photo_id": photo_id,
                        "url": photo.get("url"),
                        "job_id": job["job_id"],
                        "ratings_today": today_ratings,
                        "progress": progress,
                        "is_pro": tier == "pro"
                    }
    
    raise HTTPException(status_code=404, detail="No photos to rate right now")

@api_router.post("/rate/submit")
async def submit_rating(data: RatingSubmit, request: Request):
    user = await get_current_user(request)
    tier = user.get("tier", "free")
    
    if not data.comment or not data.comment.strip():
        raise HTTPException(status_code=400, detail="Comment is required")
    
    # Check if already rated
    existing = await db.ratings.find_one(
        {"rater_id": user["user_id"], "photo_id": data.photo_id},
        {"_id": 0}
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already rated this photo")
    
    rating_doc = {
        "rating_id": str(uuid.uuid4()),
        "rater_id": user["user_id"],
        "rater_tier": tier,
        "photo_id": data.photo_id,
        "confident": data.confident,
        "approachable": data.approachable,
        "attractive": data.attractive,
        "tags": data.tags,
        "comment": data.comment,
        "rater_gender": user.get("gender"),
        "rater_orientation": user.get("orientation"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.ratings.insert_one(rating_doc)
    
    # Update ratings given
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$inc": {"ratings_given": 1}}
    )
    
    # Pro users don't earn credits
    earned_credit = False
    ratings_until_credit = TIER_CONFIG["free"]["ratings_for_credit"]
    
    if tier != "pro":
        # Increment ratings_since_last_credit counter
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$inc": {"ratings_since_last_credit": 1}}
        )
        updated_user = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
        counter = updated_user.get("ratings_since_last_credit", 0)
        
        if counter >= TIER_CONFIG["free"]["ratings_for_credit"]:
            # Check daily earning limit
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            credits_earned_today = await db.credit_earnings.count_documents({
                "user_id": user["user_id"],
                "created_at": {"$gte": today_start.isoformat()}
            })
            
            if credits_earned_today < TIER_CONFIG["free"]["max_daily_earned_credits"]:
                await db.users.update_one(
                    {"user_id": user["user_id"]},
                    {"$set": {"ratings_since_last_credit": 0}, "$inc": {"credits": 1}}
                )
                await db.credit_earnings.insert_one({
                    "user_id": user["user_id"],
                    "amount": 1,
                    "reason": "rating_reward",
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                earned_credit = True
                counter = 0
        
        ratings_until_credit = TIER_CONFIG["free"]["ratings_for_credit"] - counter
    
    # Update photo owner's ratings earned
    photo = await db.photos.find_one({"photo_id": data.photo_id}, {"_id": 0})
    if photo:
        await db.users.update_one(
            {"user_id": photo.get("user_id")},
            {"$inc": {"ratings_earned": 1}}
        )
    
    return {
        "message": "Rating submitted",
        "earned_credit": earned_credit,
        "ratings_until_credit": ratings_until_credit if tier != "pro" else None,
        "is_pro": tier == "pro"
    }

@api_router.post("/rate/report")
async def report_photo(request: Request, photo_id: str):
    user = await get_current_user(request)

    # Prevent duplicate reports from same user
    existing_report = await db.reports.find_one({
        "reporter_id": user["user_id"],
        "photo_id": photo_id
    })
    if existing_report:
        return {"message": "Already reported"}

    await db.reports.insert_one({
        "report_id": str(uuid.uuid4()),
        "reporter_id": user["user_id"],
        "photo_id": photo_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    # Increment report count on photo
    await db.photos.update_one(
        {"photo_id": photo_id},
        {"$inc": {"report_count": 1}}
    )

    # Auto-hide photo if it reaches 3 reports
    photo = await db.photos.find_one({"photo_id": photo_id}, {"_id": 0})
    if photo and photo.get("report_count", 0) >= 3:
        await db.photos.update_one(
            {"photo_id": photo_id},
            {"$set": {"is_deleted": True}}
        )
        # Also mark the job as needing review if this was the only photo
        logger.warning(f"Photo {photo_id} auto-hidden after 3 reports")

    return {"message": "Photo reported. Thank you for keeping MatchMe safe."}

# ==================== DASHBOARD ====================
@api_router.get("/user/dashboard")
async def get_dashboard(request: Request):
    user = await get_current_user(request)
    tier = user.get("tier", "free")
    
    # Get recent jobs
    jobs = await db.jobs.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(5)
    
    # Get rating stats for today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_ratings = await db.ratings.count_documents({
        "rater_id": user["user_id"],
        "created_at": {"$gte": today_start.isoformat()}
    })
    
    credits_earned_today = await db.credit_earnings.count_documents({
        "user_id": user["user_id"],
        "created_at": {"$gte": today_start.isoformat()}
    })
    
    tier_config = TIER_CONFIG.get(tier, TIER_CONFIG["free"])
    
    return {
        "user": {
            "user_id": user["user_id"],
            "name": user.get("name"),
            "email": user.get("email"),
            "credits": user.get("credits", 0) if tier != "pro" else None,
            "tier": tier
        },
        "recent_jobs": jobs,
        "stats": {
            "ratings_today": today_ratings,
            "credits_earned_today": credits_earned_today if tier != "pro" else None,
            "can_earn_more": credits_earned_today < TIER_CONFIG["free"]["max_daily_earned_credits"] if tier != "pro" else None,
            "ratings_for_credit": TIER_CONFIG["free"]["ratings_for_credit"] if tier != "pro" else None,
            "is_pro": tier == "pro"
        },
        "tier_info": {
            "min_ratings": tier_config.get("min_ratings"),
            "time_cap_hours": tier_config.get("time_cap_hours"),
            "unlimited": tier_config.get("unlimited", False)
        }
    }

# ==================== BACKGROUND JOB WORKER ====================
async def get_job_ratings_count(job_id: str) -> int:
    """Get total number of ratings for all photos in a job"""
    job = await db.jobs.find_one({"job_id": job_id}, {"_id": 0})
    if not job:
        return 0
    
    count = 0
    for photo_id in job.get("photo_ids", []):
        photo_ratings = await db.ratings.count_documents({"photo_id": photo_id})
        count += photo_ratings
    return count

async def process_job(job_id: str, low_confidence: bool = False):
    """Process a job and generate results"""
    job = await db.jobs.find_one({"job_id": job_id}, {"_id": 0})
    if not job:
        logger.error(f"Job {job_id} not found for processing")
        return
    
    # Get all ratings for photos in this job
    photo_scores = []
    all_rater_ids = set()
    
    for photo_id in job.get("photo_ids", []):
        photo_ratings = await db.ratings.find({"photo_id": photo_id}, {"_id": 0}).to_list(100)
        
        if photo_ratings:
            # Weighted formula: (avg_confident × 0.4) + (avg_approachable × 0.35) + (avg_attractive × 0.25)
            avg_confident = sum(r["confident"] for r in photo_ratings) / len(photo_ratings)
            avg_approachable = sum(r["approachable"] for r in photo_ratings) / len(photo_ratings)
            avg_attractive = sum(r["attractive"] for r in photo_ratings) / len(photo_ratings)
            
            photo_score = (avg_confident * 0.4) + (avg_approachable * 0.35) + (avg_attractive * 0.25)
            
            # Build individual ratings with rater usernames
            individual_ratings = []
            for r in photo_ratings:
                all_rater_ids.add(r["rater_id"])
                rater_user = await db.users.find_one({"user_id": r["rater_id"]}, {"_id": 0, "name": 1})
                individual_ratings.append({
                    "rater_username": rater_user.get("name", "Anonymous") if rater_user else "Anonymous",
                    "confident": r["confident"],
                    "approachable": r["approachable"],
                    "attractive": r["attractive"],
                    "comment": r.get("comment", ""),
                    "tags": r.get("tags", [])
                })
            
            photo_scores.append({
                "photo_id": photo_id,
                "photo_score": photo_score,
                "avg_confident": avg_confident,
                "avg_approachable": avg_approachable,
                "avg_attractive": avg_attractive,
                "rating_count": len(photo_ratings),
                "ratings": individual_ratings,
                "comments": [r["comment"] for r in photo_ratings if r.get("comment")],
                "tags": [tag for r in photo_ratings for tag in r.get("tags", [])]
            })
        else:
            photo_scores.append({
                "photo_id": photo_id,
                "photo_score": 0,
                "avg_confident": 0,
                "avg_approachable": 0,
                "avg_attractive": 0,
                "rating_count": 0,
                "ratings": [],
                "comments": [],
                "tags": []
            })
    
    # Sort by photo_score descending
    photo_scores.sort(key=lambda x: x["photo_score"], reverse=True)
    
    # Flag lowest-scoring photo as "remove this"
    if photo_scores:
        photo_scores[-1]["remove_this"] = True
    
    total_raters = len(all_rater_ids)
    
    result = {
        "winner": photo_scores[0] if photo_scores else None,
        "ranked": photo_scores,
        "total_raters": total_raters,
        "low_confidence": low_confidence,
        "processed_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Update job
    await db.jobs.update_one(
        {"job_id": job_id},
        {"$set": {
            "status": "complete",
            "result": result,
            "low_confidence": low_confidence,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Send email notification
    job_user = await db.users.find_one({"user_id": job["user_id"]}, {"_id": 0})
    if job_user:
        await send_results_email(
            user_email=job_user.get("email"),
            user_name=job_user.get("name", "there"),
            job_type=job["type"],
            job_id=job_id,
            rater_count=total_raters,
            low_confidence=low_confidence
        )
    
    # Award bonus to each rater via counter (skip Pro raters)
    # Every 5 job completions where user was a rater = 1 whole credit
    for rater_id in all_rater_ids:
        rater = await db.users.find_one({"user_id": rater_id}, {"_id": 0})
        if rater and rater.get("tier") != "pro":
            await db.users.update_one(
                {"user_id": rater_id},
                {"$inc": {"job_bonus_count": 1}}
            )
            updated_rater = await db.users.find_one({"user_id": rater_id}, {"_id": 0})
            if updated_rater.get("job_bonus_count", 0) >= 5:
                await db.users.update_one(
                    {"user_id": rater_id},
                    {"$set": {"job_bonus_count": 0}, "$inc": {"credits": 1}}
                )
                await db.credit_earnings.insert_one({
                    "user_id": rater_id,
                    "amount": 1,
                    "reason": "job_completion_bonus",
                    "job_id": job_id,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
    
    logger.info(f"Job {job_id} processed successfully with {total_raters} raters")

async def fail_job(job_id: str, refund: bool = False, refund_amount: int = 0):
    """Mark a job as failed and optionally refund credits"""
    job = await db.jobs.find_one({"job_id": job_id}, {"_id": 0})
    if not job:
        return
    
    # Update job status
    await db.jobs.update_one(
        {"job_id": job_id},
        {"$set": {
            "status": "failed",
            "completed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Refund credits if applicable
    if refund and refund_amount > 0:
        await db.users.update_one(
            {"user_id": job["user_id"]},
            {"$inc": {"credits": refund_amount}}
        )
    
    # Send apology email
    job_user = await db.users.find_one({"user_id": job["user_id"]}, {"_id": 0})
    if job_user:
        await send_job_failed_email(
            user_email=job_user.get("email"),
            user_name=job_user.get("name", "there"),
            job_type=job["type"],
            refunded=refund,
            refund_amount=refund_amount
        )
    
    logger.info(f"Job {job_id} marked as failed, refund={refund}, amount={refund_amount}")

async def run_job_worker():
    """Background job worker - runs every 15 minutes"""
    logger.info("Running job worker...")
    
    # Get all queued or processing jobs
    jobs = await db.jobs.find(
        {"status": {"$in": ["queued", "processing"]}},
        {"_id": 0}
    ).to_list(100)
    
    now = datetime.now(timezone.utc)
    
    for job in jobs:
        job_id = job["job_id"]
        tier = job.get("tier", "free")
        tier_config = TIER_CONFIG.get(tier, TIER_CONFIG["free"])
        
        created_at = datetime.fromisoformat(job["created_at"])
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        
        time_elapsed = now - created_at
        hours_elapsed = time_elapsed.total_seconds() / 3600
        
        # Get ratings count for this job
        ratings_count = await get_job_ratings_count(job_id)
        
        min_ratings = tier_config["min_ratings"]
        time_cap_hours = tier_config["time_cap_hours"]
        low_confidence_min = tier_config["low_confidence_min"]
        extension_hours = tier_config["extension_hours"]
        
        # Check extension status
        extended = job.get("extended", False)
        extension_count = job.get("extension_count", 0)
        
        # Calculate effective time cap (with extension if applied)
        effective_time_cap = time_cap_hours
        if extended:
            effective_time_cap = time_cap_hours + extension_hours
        
        # Condition 1: Has ratings_count reached the tier minimum?
        if ratings_count >= min_ratings:
            logger.info(f"Job {job_id}: Processing with {ratings_count} ratings (min={min_ratings})")
            await process_job(job_id, low_confidence=False)
            continue
        
        # Condition 2: Has time since submission exceeded the tier time cap?
        if hours_elapsed >= effective_time_cap:
            # Check if we have enough for low confidence processing
            if ratings_count >= low_confidence_min:
                logger.info(f"Job {job_id}: Processing with low confidence ({ratings_count} ratings at {hours_elapsed:.1f}hrs)")
                await process_job(job_id, low_confidence=True)
            elif not extended and extension_count == 0:
                # Apply extension
                logger.info(f"Job {job_id}: Extending by {extension_hours} hours (only {ratings_count} ratings)")
                await db.jobs.update_one(
                    {"job_id": job_id},
                    {"$set": {"extended": True, "extension_count": 1}}
                )
            else:
                # Already extended, job fails
                logger.info(f"Job {job_id}: Failing - insufficient ratings after extension")
                
                # Determine refund
                refund = False
                refund_amount = 0
                
                if tier == "free":
                    refund = True
                    refund_amount = 1  # Refund 1 credit
                elif tier == "priority":
                    refund = True
                    refund_amount = 1  # Refund 1 credit from monthly balance
                # Pro tier: no refund
                
                await fail_job(job_id, refund=refund, refund_amount=refund_amount)
        
        # Update job status to processing if not already
        if job["status"] == "queued":
            await db.jobs.update_one(
                {"job_id": job_id},
                {"$set": {"status": "processing"}}
            )
    
    logger.info(f"Job worker completed. Processed {len(jobs)} jobs.")

# API endpoint to trigger job worker manually (for testing)
@api_router.post("/admin/run-worker")
async def trigger_job_worker(request: Request):
    """Admin endpoint to manually trigger the job worker"""
    user = await get_current_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    await run_job_worker()
    return {"message": "Job worker executed"}

# ==================== RAZORPAY SUBSCRIPTIONS ====================
RAZORPAY_PRODUCTS = {
    "priority": {
        "name": "Priority",
        "price_inr": 749,  # ₹749/month (~$9)
        "price_paise": 74900,
        "credits": 12,
        "period": "monthly",
        "interval": 1,
    },
    "pro": {
        "name": "Pro",
        "price_inr": 2099,  # ₹2099/month (~$25)
        "price_paise": 209900,
        "credits": None,  # Unlimited
        "period": "monthly",
        "interval": 1,
    }
}

# Cache for Razorpay plan IDs (created once, reused)
_razorpay_plan_ids = {}

async def get_or_create_razorpay_plan(package_id: str) -> str:
    """Get or create a Razorpay plan for a package"""
    global _razorpay_plan_ids
    
    if package_id in _razorpay_plan_ids:
        return _razorpay_plan_ids[package_id]
    
    # Check DB for cached plan ID
    plan_doc = await db.razorpay_plans.find_one({"package_id": package_id}, {"_id": 0})
    if plan_doc:
        _razorpay_plan_ids[package_id] = plan_doc["plan_id"]
        return plan_doc["plan_id"]
    
    # Create new plan in Razorpay
    product = RAZORPAY_PRODUCTS[package_id]
    plan_data = {
        "period": product["period"],
        "interval": product["interval"],
        "item": {
            "name": f"MatchMe {product['name']}",
            "amount": product["price_paise"],
            "currency": "INR",
            "description": f"MatchMe {product['name']} - Monthly Subscription"
        }
    }
    
    plan = await asyncio.to_thread(razorpay_client.plan.create, data=plan_data)
    plan_id = plan["id"]
    
    # Cache it
    _razorpay_plan_ids[package_id] = plan_id
    await db.razorpay_plans.insert_one({
        "package_id": package_id,
        "plan_id": plan_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    logger.info(f"Created Razorpay plan {plan_id} for {package_id}")
    return plan_id

@api_router.post("/payments/subscribe")
async def create_subscription(data: CheckoutRequest, request: Request):
    """Create a Razorpay subscription for checkout"""
    user = await get_current_user(request)
    
    if not razorpay_client:
        logger.error("Razorpay is not configured")
        raise HTTPException(status_code=500, detail="Payment system not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.")
    
    if data.package_id not in RAZORPAY_PRODUCTS:
        raise HTTPException(status_code=400, detail="Invalid package")
    
    try:
        # Get or create the plan
        plan_id = await get_or_create_razorpay_plan(data.package_id)
        
        # Create subscription
        sub_data = {
            "plan_id": plan_id,
            "customer_notify": 1,
            "total_count": 12,  # 12 billing cycles max
            "notes": {
                "user_id": user["user_id"],
                "package_id": data.package_id
            }
        }
        
        subscription = await asyncio.to_thread(razorpay_client.subscription.create, data=sub_data)
        
        return {
            "subscription_id": subscription["id"],
            "razorpay_key_id": RAZORPAY_KEY_ID,
            "amount": RAZORPAY_PRODUCTS[data.package_id]["price_paise"],
            "currency": "INR",
            "name": f"MatchMe {RAZORPAY_PRODUCTS[data.package_id]['name']}",
            "description": f"MatchMe {RAZORPAY_PRODUCTS[data.package_id]['name']} Monthly Subscription",
            "prefill": {
                "name": user.get("name", ""),
                "email": user.get("email", "")
            }
        }
    
    except Exception as e:
        logger.error(f"Razorpay subscription error: {e}")
        raise HTTPException(status_code=500, detail=f"Payment error: {str(e)}")

@api_router.post("/payments/verify")
async def verify_payment(data: RazorpayVerifyRequest, request: Request):
    """Verify Razorpay payment signature and activate subscription"""
    user = await get_current_user(request)
    
    if not razorpay_client:
        raise HTTPException(status_code=500, detail="Payment system not configured")
    
    try:
        # Verify the payment signature
        params_dict = {
            "razorpay_payment_id": data.razorpay_payment_id,
            "razorpay_subscription_id": data.razorpay_subscription_id,
            "razorpay_signature": data.razorpay_signature
        }
        
        await asyncio.to_thread(
            razorpay_client.utility.verify_payment_signature, params_dict
        )
        
        # Signature verified — activate the subscription
        package_id = data.package_id
        if package_id not in RAZORPAY_PRODUCTS:
            raise HTTPException(status_code=400, detail="Invalid package")
        
        update_fields = {
            "tier": package_id,
            "razorpay_subscription_id": data.razorpay_subscription_id,
            "razorpay_payment_id": data.razorpay_payment_id,
            "subscription_start_date": datetime.now(timezone.utc).isoformat()
        }
        
        if package_id == "priority":
            update_fields["credits"] = RAZORPAY_PRODUCTS["priority"]["credits"]
        
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$set": update_fields}
        )
        
        logger.info(f"Subscription activated for {user['user_id']}: {package_id}")
        
        return {
            "status": "success",
            "tier": package_id,
            "message": f"Welcome to MatchMe {RAZORPAY_PRODUCTS[package_id]['name']}!"
        }
    
    except razorpay.errors.SignatureVerificationError:
        logger.error(f"Payment signature verification failed for user {user['user_id']}")
        raise HTTPException(status_code=400, detail="Payment verification failed. Please contact support.")
    except Exception as e:
        logger.error(f"Payment verification error: {e}")
        raise HTTPException(status_code=500, detail=f"Payment verification error: {str(e)}")

@api_router.post("/webhook/razorpay")
async def razorpay_webhook(request: Request):
    """Handle Razorpay webhooks for subscription events"""
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    
    # Verify webhook signature if secret is set
    if RAZORPAY_WEBHOOK_SECRET:
        try:
            await asyncio.to_thread(
                razorpay_client.utility.verify_webhook_signature,
                body.decode("utf-8"), signature, RAZORPAY_WEBHOOK_SECRET
            )
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
    
    import json as _json
    try:
        payload = _json.loads(body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payload")
    
    event = payload.get("event", "")
    payment_entity = payload.get("payload", {})
    
    logger.info(f"Razorpay webhook: {event}")
    
    if event == "subscription.charged":
        # Recurring payment successful — renew credits for Priority
        sub_entity = payment_entity.get("subscription", {}).get("entity", {})
        subscription_id = sub_entity.get("id")
        
        if subscription_id:
            user = await db.users.find_one({"razorpay_subscription_id": subscription_id}, {"_id": 0})
            if user and user.get("tier") == "priority":
                await db.users.update_one(
                    {"user_id": user["user_id"]},
                    {"$set": {
                        "credits": RAZORPAY_PRODUCTS["priority"]["credits"],
                        "subscription_start_date": datetime.now(timezone.utc).isoformat()
                    }}
                )
                logger.info(f"Priority credits renewed for {user['user_id']}")
    
    elif event in ("subscription.cancelled", "subscription.completed"):
        sub_entity = payment_entity.get("subscription", {}).get("entity", {})
        subscription_id = sub_entity.get("id")
        
        if subscription_id:
            user = await db.users.find_one({"razorpay_subscription_id": subscription_id}, {"_id": 0})
            if user:
                await db.users.update_one(
                    {"user_id": user["user_id"]},
                    {"$set": {
                        "tier": "free",
                        "razorpay_subscription_id": None
                    }}
                )
                logger.info(f"Subscription ended for {user['user_id']}, downgraded to free")
    
    return {"received": True}

@api_router.post("/payments/cancel-subscription")
async def cancel_subscription(request: Request):
    """Cancel user's subscription"""
    user = await get_current_user(request)
    
    subscription_id = user.get("razorpay_subscription_id")
    if not subscription_id:
        raise HTTPException(status_code=400, detail="No active subscription")
    
    try:
        await asyncio.to_thread(
            razorpay_client.subscription.cancel, subscription_id
        )
        
        # Update user immediately for UX (webhook will also fire)
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$set": {"tier": "free", "razorpay_subscription_id": None}}
        )
        
        return {"message": "Subscription cancelled"}
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/admin/reports")
async def get_reported_photos(request: Request):
    """Admin endpoint to review reported photos"""
    user = await get_current_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    # Get photos with 1+ reports (including auto-hidden ones)
    pipeline = [
        {"$match": {"report_count": {"$gte": 1}}},
        {"$sort": {"report_count": -1}},
        {"$limit": 50}
    ]
    photos = await db.photos.aggregate(pipeline).to_list(50)
    for p in photos:
        p.pop("_id", None)
    return photos

@api_router.post("/admin/photos/{photo_id}/restore")
async def restore_photo(photo_id: str, request: Request):
    """Admin: restore a falsely reported photo"""
    user = await get_current_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    await db.photos.update_one(
        {"photo_id": photo_id},
        {"$set": {"is_deleted": False, "report_count": 0}}
    )
    # Clear all reports for this photo
    await db.reports.delete_many({"photo_id": photo_id})
    return {"message": "Photo restored"}

@api_router.delete("/admin/photos/{photo_id}")
async def admin_delete_photo(photo_id: str, request: Request):
    """Admin: permanently remove a reported photo"""
    user = await get_current_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    photo = await db.photos.find_one({"photo_id": photo_id}, {"_id": 0})
    if photo:
        try:
            await asyncio.to_thread(
                cloudinary.uploader.destroy,
                photo["public_id"],
                invalidate=True
            )
        except Exception as e:
            logger.error(f"Cloudinary delete failed: {e}")
    
    await db.photos.update_one({"photo_id": photo_id}, {"$set": {"is_deleted": True}})
    return {"message": "Photo deleted"}

# ==================== HEALTH CHECK ====================
@api_router.get("/")
async def root():
    return {"message": "MatchMe API", "status": "healthy"}

@api_router.get("/health")
async def health():
    return {"status": "ok"}
# CORS
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://matchme-two.vercel.app")
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[
        FRONTEND_URL,
        "https://matchme-two.vercel.app",
        "https://matchme-three.vercel.app",
        "https://matchme-gje02qajp-bigdawws-projects.vercel.app",
        "http://localhost:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the router in the main app
app.include_router(api_router)



# ==================== BACKGROUND TASK SCHEDULER ====================
async def scheduler():
    """Run job worker every 15 minutes"""
    while True:
        try:
            await run_job_worker()
        except Exception as e:
            logger.error(f"Job worker error: {e}")
        await asyncio.sleep(15 * 60)  # 15 minutes

# ==================== STARTUP ====================
@app.on_event("startup")
async def startup():
    try:
        await db.command("ping")
        logger.info("Connected to MongoDB Atlas")
        
        # Create indexes
        await db.users.create_index("email", unique=True)
        await db.users.create_index("user_id", unique=True)
        await db.users.create_index("razorpay_subscription_id", sparse=True)
        await db.photos.create_index("user_id")
        await db.photos.create_index("photo_id", unique=True)
        await db.jobs.create_index("user_id")
        await db.jobs.create_index("job_id", unique=True)
        await db.jobs.create_index("status")
        await db.ratings.create_index([("rater_id", 1), ("photo_id", 1)], unique=True)
        await db.login_attempts.create_index("identifier")
        
        # Seed admin user
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@matchme.com")
        admin_password = os.environ.get("ADMIN_PASSWORD", "AdminMatch2024!")
        existing = await db.users.find_one({"email": admin_email}, {"_id": 0})
        
        if existing is None:
            admin_id = f"user_{uuid.uuid4().hex[:12]}"
            hashed = hash_password(admin_password)
            await db.users.insert_one({
                "user_id": admin_id,
                "email": admin_email,
                "name": "Admin",
                "password_hash": hashed,
                "credits": 999,
                "gender": None,
                "orientation": None,
                "dating_app": None,
                "tier": "pro",
                "stripe_customer_id": None,
                "stripe_subscription_id": None,
                "razorpay_subscription_id": None,
                "razorpay_payment_id": None,
                "ratings_given": 0,
                "ratings_earned": 0,
                "onboarding_completed": True,
                "role": "admin",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            logger.info(f"Admin user created: {admin_email}")
        
        # Start background scheduler
        asyncio.create_task(scheduler())
        logger.info("Background job scheduler started (15 min interval)")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
    
    logger.info("Cloudinary configured")
    logger.info("Resend email configured")
    if razorpay_client:
        logger.info(f"Razorpay configured (key: {RAZORPAY_KEY_ID[:12]}...)")
    else:
        logger.warning("⚠️  RAZORPAY_KEY_ID/RAZORPAY_KEY_SECRET not set — payments will fail!")
    
    # Write test credentials
    os.makedirs("memory", exist_ok=True)
    with open("memory/test_credentials.md", "w") as f:
        f.write(f"""# Test Credentials

## Admin Account
- Email: admin@matchme.com
- Password: AdminMatch2024!
- Role: admin

## Tier Structure
- Free: 3 ratings OR 24hrs, 3 credits on signup, earn 1 per 5 ratings
- Priority ($9/mo): 7 ratings OR 4hrs, 12 credits/month
- Pro ($25/mo): 10 ratings OR 4hrs, unlimited uploads, no credits

## Credit Costs
- Best Shot: 1 credit
- Profile Analysis: 2 credits

## Background Worker
- Runs every 15 minutes
- Processes jobs based on tier conditions
- Awards 0.2 credits to raters on job completion

## API Endpoints
- POST /api/auth/register
- POST /api/auth/login
- POST /api/payments/subscribe (subscriptions)
- POST /api/admin/run-worker (manual worker trigger)
""")
    logger.info("Test credentials written")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
