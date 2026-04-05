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
import requests
from bson import ObjectId
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutSessionRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_ALGORITHM = "HS256"
JWT_SECRET = os.environ.get('JWT_SECRET')

# Object Storage Configuration
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = "matchme"
storage_key = None

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

# ==================== OBJECT STORAGE ====================
def init_storage():
    global storage_key
    if storage_key:
        return storage_key
    resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY}, timeout=30)
    resp.raise_for_status()
    storage_key = resp.json()["storage_key"]
    return storage_key

def put_object(path: str, data: bytes, content_type: str) -> dict:
    key = init_storage()
    resp = requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data, timeout=120
    )
    resp.raise_for_status()
    return resp.json()

def get_object(path: str) -> tuple:
    key = init_storage()
    resp = requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key}, timeout=60
    )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")

# ==================== PYDANTIC MODELS ====================
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
    credits: int
    gender: Optional[str] = None
    orientation: Optional[str] = None
    dating_app: Optional[str] = None
    tier: str
    onboarding_completed: bool

class OnboardingData(BaseModel):
    gender: str
    orientation: str
    dating_app: str

class PhotoResponse(BaseModel):
    photo_id: str
    url: str
    storage_path: str
    created_at: str

class JobCreate(BaseModel):
    photo_ids: List[str]
    bio: Optional[str] = None
    prompt_answer: Optional[str] = None

class JobResponse(BaseModel):
    job_id: str
    type: str
    status: str
    priority: str
    created_at: str
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

class RatingSubmit(BaseModel):
    photo_id: str
    confident: int = Field(ge=1, le=5)
    approachable: int = Field(ge=1, le=5)
    attractive: int = Field(ge=1, le=5)
    tags: List[str] = []
    comment: str

class CheckoutRequest(BaseModel):
    package_id: str
    origin_url: str

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
        "credits": 3,
        "gender": None,
        "orientation": None,
        "dating_app": None,
        "tier": "free",
        "ratings_given": 0,
        "ratings_earned": 0,
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
        "credits": 3,
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
        # Increment failed attempts
        await db.login_attempts.update_one(
            {"identifier": identifier},
            {"$inc": {"count": 1}, "$set": {"last_attempt": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Clear failed attempts
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
    
    # REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    auth_response = requests.get(
        "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
        headers={"X-Session-ID": session_id},
        timeout=30
    )
    if auth_response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    data = auth_response.json()
    email = data["email"].lower()
    
    # Find or create user
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
            "credits": 3,
            "gender": None,
            "orientation": None,
            "dating_app": None,
            "tier": "free",
            "ratings_given": 0,
            "ratings_earned": 0,
            "onboarding_completed": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
        user = user_doc
    else:
        user_id = user["user_id"]
        # Update google info
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

# ==================== FILE UPLOAD ====================
@api_router.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    user = await get_current_user(request)
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPG/PNG images allowed")
    
    # Read file (max 10MB)
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    photo_id = str(uuid.uuid4())
    path = f"{APP_NAME}/uploads/{user['user_id']}/{photo_id}.{ext}"
    
    result = put_object(path, data, file.content_type or "image/jpeg")
    
    photo_doc = {
        "photo_id": photo_id,
        "user_id": user["user_id"],
        "storage_path": result["path"],
        "original_filename": file.filename,
        "content_type": file.content_type,
        "size": result.get("size", len(data)),
        "is_deleted": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.photos.insert_one(photo_doc)
    
    return {
        "photo_id": photo_id,
        "storage_path": result["path"],
        "created_at": photo_doc["created_at"]
    }

@api_router.get("/files/{path:path}")
async def download_file(path: str, request: Request, auth: str = Query(None)):
    # Check auth
    try:
        if auth:
            payload = jwt.decode(auth, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "access":
                raise HTTPException(status_code=401, detail="Invalid token")
        else:
            await get_current_user(request)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    record = await db.photos.find_one({"storage_path": path, "is_deleted": False}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    
    data, content_type = get_object(path)
    return Response(content=data, media_type=record.get("content_type", content_type))

@api_router.get("/user/photos")
async def get_user_photos(request: Request):
    user = await get_current_user(request)
    photos = await db.photos.find(
        {"user_id": user["user_id"], "is_deleted": False},
        {"_id": 0}
    ).to_list(100)
    return photos

# ==================== JOBS ====================
@api_router.post("/jobs/best-shot")
async def create_best_shot_job(data: JobCreate, request: Request):
    user = await get_current_user(request)
    
    if len(data.photo_ids) < 3 or len(data.photo_ids) > 10:
        raise HTTPException(status_code=400, detail="Upload 3-10 photos")
    
    if user["credits"] < 1:
        raise HTTPException(status_code=400, detail="Not enough credits")
    
    job_id = str(uuid.uuid4())
    priority = "paid" if user["tier"] in ["priority", "pro"] else "free"
    
    job_doc = {
        "job_id": job_id,
        "user_id": user["user_id"],
        "type": "best-shot",
        "status": "queued",
        "photo_ids": data.photo_ids,
        "priority": priority,
        "result": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None
    }
    await db.jobs.insert_one(job_doc)
    
    # Deduct credit
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$inc": {"credits": -1}}
    )
    
    return {"job_id": job_id, "status": "queued", "priority": priority}

@api_router.post("/jobs/profile-analysis")
async def create_profile_analysis_job(data: JobCreate, request: Request):
    user = await get_current_user(request)
    
    if len(data.photo_ids) < 4 or len(data.photo_ids) > 6:
        raise HTTPException(status_code=400, detail="Upload 4-6 photos")
    
    if user["credits"] < 2:
        raise HTTPException(status_code=400, detail="Not enough credits (need 2)")
    
    job_id = str(uuid.uuid4())
    priority = "paid" if user["tier"] in ["priority", "pro"] else "free"
    
    job_doc = {
        "job_id": job_id,
        "user_id": user["user_id"],
        "type": "profile-analysis",
        "status": "queued",
        "photo_ids": data.photo_ids,
        "bio": data.bio,
        "prompt_answer": data.prompt_answer,
        "priority": priority,
        "result": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None
    }
    await db.jobs.insert_one(job_doc)
    
    # Deduct credits
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$inc": {"credits": -2}}
    )
    
    return {"job_id": job_id, "status": "queued", "priority": priority}

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
    
    # Check daily limit
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_ratings = await db.ratings.count_documents({
        "rater_id": user["user_id"],
        "created_at": {"$gte": today_start.isoformat()}
    })
    
    if today_ratings >= 25:  # Max 5 credits/day * 5 ratings each
        raise HTTPException(status_code=400, detail="Daily rating limit reached")
    
    # Find photo to rate (gender matched)
    user_orientation = user.get("orientation", "everyone")
    
    # Build query for gender matching
    gender_filter = {}
    if user_orientation == "men":
        gender_filter = {"user_gender": "man"}
    elif user_orientation == "women":
        gender_filter = {"user_gender": "woman"}
    
    # Find photos from queued jobs that user hasn't rated yet
    rated_photo_ids = await db.ratings.distinct("photo_id", {"rater_id": user["user_id"]})
    
    # Get a queued job's photo
    pipeline = [
        {"$match": {"status": "queued"}},
        {"$sort": {"priority": -1, "created_at": 1}},  # Priority jobs first
        {"$limit": 10}
    ]
    jobs = await db.jobs.aggregate(pipeline).to_list(10)
    
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
        
        # Get first unrated photo from this job
        for photo_id in job.get("photo_ids", []):
            if photo_id not in rated_photo_ids:
                photo = await db.photos.find_one({"photo_id": photo_id, "is_deleted": False}, {"_id": 0})
                if photo:
                    return {
                        "photo_id": photo_id,
                        "storage_path": photo["storage_path"],
                        "job_id": job["job_id"],
                        "ratings_today": today_ratings,
                        "progress": today_ratings % 5
                    }
    
    raise HTTPException(status_code=404, detail="No photos to rate right now")

@api_router.post("/rate/submit")
async def submit_rating(data: RatingSubmit, request: Request):
    user = await get_current_user(request)
    
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
    
    # Check if user earns a credit (every 5 ratings)
    updated_user = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
    ratings_given = updated_user.get("ratings_given", 0)
    
    earned_credit = False
    if ratings_given % 5 == 0:
        # Check daily earning limit (max 5 credits/day)
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        credits_earned_today = await db.credit_earnings.count_documents({
            "user_id": user["user_id"],
            "created_at": {"$gte": today_start.isoformat()}
        })
        
        if credits_earned_today < 5:
            await db.users.update_one(
                {"user_id": user["user_id"]},
                {"$inc": {"credits": 1}}
            )
            await db.credit_earnings.insert_one({
                "user_id": user["user_id"],
                "amount": 1,
                "reason": "rating_reward",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            earned_credit = True
    
    # Check if job has enough ratings to complete (simulate with 3+ ratings)
    photo = await db.photos.find_one({"photo_id": data.photo_id}, {"_id": 0})
    if photo:
        photo_owner = photo.get("user_id")
        await db.users.update_one(
            {"user_id": photo_owner},
            {"$inc": {"ratings_earned": 1}}
        )
    
    return {
        "message": "Rating submitted",
        "earned_credit": earned_credit,
        "ratings_until_credit": 5 - (ratings_given % 5) if not earned_credit else 5
    }

@api_router.post("/rate/report")
async def report_photo(request: Request, photo_id: str):
    user = await get_current_user(request)
    await db.reports.insert_one({
        "report_id": str(uuid.uuid4()),
        "reporter_id": user["user_id"],
        "photo_id": photo_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    return {"message": "Photo reported"}

# ==================== DASHBOARD ====================
@api_router.get("/user/dashboard")
async def get_dashboard(request: Request):
    user = await get_current_user(request)
    
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
    
    return {
        "user": {
            "user_id": user["user_id"],
            "name": user.get("name"),
            "email": user.get("email"),
            "credits": user.get("credits", 0),
            "tier": user.get("tier", "free")
        },
        "recent_jobs": jobs,
        "stats": {
            "ratings_today": today_ratings,
            "credits_earned_today": credits_earned_today,
            "can_earn_more": credits_earned_today < 5
        }
    }

# ==================== PAYMENTS ====================
PACKAGES = {
    "priority_pass": {"amount": 9.00, "name": "Priority Pass", "credits": 5, "tier_upgrade": "priority"},
    "pro_monthly": {"amount": 19.00, "name": "Pro Monthly", "credits": 0, "tier_upgrade": "pro"}
}

@api_router.post("/payments/checkout")
async def create_checkout(data: CheckoutRequest, request: Request):
    user = await get_current_user(request)
    
    if data.package_id not in PACKAGES:
        raise HTTPException(status_code=400, detail="Invalid package")
    
    package = PACKAGES[data.package_id]
    
    webhook_url = f"{request.base_url}api/webhook/stripe"
    stripe_checkout = StripeCheckout(
        api_key=os.environ.get("STRIPE_API_KEY"),
        webhook_url=webhook_url
    )
    
    success_url = f"{data.origin_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{data.origin_url}/pricing"
    
    checkout_request = CheckoutSessionRequest(
        amount=package["amount"],
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": user["user_id"],
            "package_id": data.package_id,
            "package_name": package["name"]
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Create payment transaction record
    await db.payment_transactions.insert_one({
        "transaction_id": str(uuid.uuid4()),
        "session_id": session.session_id,
        "user_id": user["user_id"],
        "package_id": data.package_id,
        "amount": package["amount"],
        "currency": "usd",
        "status": "pending",
        "payment_status": "initiated",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"url": session.url, "session_id": session.session_id}

@api_router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str, request: Request):
    user = await get_current_user(request)
    
    transaction = await db.payment_transactions.find_one(
        {"session_id": session_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # If already processed, return cached status
    if transaction.get("payment_status") == "paid":
        return transaction
    
    webhook_url = f"{request.base_url}api/webhook/stripe"
    stripe_checkout = StripeCheckout(
        api_key=os.environ.get("STRIPE_API_KEY"),
        webhook_url=webhook_url
    )
    
    status = await stripe_checkout.get_checkout_status(session_id)
    
    # Update transaction
    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {
            "status": status.status,
            "payment_status": status.payment_status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # If payment successful and not already processed
    if status.payment_status == "paid" and transaction.get("payment_status") != "paid":
        package = PACKAGES.get(transaction.get("package_id"))
        if package:
            update_fields = {}
            if package.get("credits"):
                update_fields["$inc"] = {"credits": package["credits"]}
            if package.get("tier_upgrade"):
                update_fields["$set"] = {"tier": package["tier_upgrade"]}
            
            if update_fields:
                await db.users.update_one(
                    {"user_id": user["user_id"]},
                    update_fields
                )
    
    return {
        "session_id": session_id,
        "status": status.status,
        "payment_status": status.payment_status,
        "amount_total": status.amount_total,
        "currency": status.currency
    }

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    try:
        webhook_url = f"{request.base_url}api/webhook/stripe"
        stripe_checkout = StripeCheckout(
            api_key=os.environ.get("STRIPE_API_KEY"),
            webhook_url=webhook_url
        )
        event = await stripe_checkout.handle_webhook(body, signature)
        
        if event.payment_status == "paid":
            session_id = event.session_id
            transaction = await db.payment_transactions.find_one(
                {"session_id": session_id},
                {"_id": 0}
            )
            
            if transaction and transaction.get("payment_status") != "paid":
                package = PACKAGES.get(transaction.get("package_id"))
                if package:
                    update_fields = {}
                    if package.get("credits"):
                        update_fields["$inc"] = {"credits": package["credits"]}
                    if package.get("tier_upgrade"):
                        update_fields["$set"] = {"tier": package["tier_upgrade"]}
                    
                    if update_fields:
                        await db.users.update_one(
                            {"user_id": transaction["user_id"]},
                            update_fields
                        )
                
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {
                        "status": "complete",
                        "payment_status": "paid",
                        "completed_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
        
        return {"received": True}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# ==================== PROCESS JOBS (Background task simulation) ====================
@api_router.post("/jobs/{job_id}/process")
async def process_job(job_id: str, request: Request):
    """Admin endpoint to simulate job processing"""
    job = await db.jobs.find_one({"job_id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "queued":
        raise HTTPException(status_code=400, detail="Job already processed")
    
    # Get ratings for photos
    ratings = []
    for photo_id in job.get("photo_ids", []):
        photo_ratings = await db.ratings.find({"photo_id": photo_id}, {"_id": 0}).to_list(100)
        ratings.append({
            "photo_id": photo_id,
            "ratings": photo_ratings,
            "avg_confident": sum(r["confident"] for r in photo_ratings) / len(photo_ratings) if photo_ratings else 0,
            "avg_approachable": sum(r["approachable"] for r in photo_ratings) / len(photo_ratings) if photo_ratings else 0,
            "avg_attractive": sum(r["attractive"] for r in photo_ratings) / len(photo_ratings) if photo_ratings else 0,
            "comments": [r["comment"] for r in photo_ratings if r.get("comment")],
            "tags": [tag for r in photo_ratings for tag in r.get("tags", [])]
        })
    
    # Sort by total score
    ratings.sort(key=lambda x: x["avg_confident"] + x["avg_approachable"] + x["avg_attractive"], reverse=True)
    
    result = {
        "winner": ratings[0] if ratings else None,
        "ranked": ratings,
        "feedback": [r["comments"] for r in ratings],
        "processed_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.jobs.update_one(
        {"job_id": job_id},
        {"$set": {
            "status": "complete",
            "result": result,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Send mock email notification
    logger.info(f"[MOCKED EMAIL] Job {job_id} completed for user {job['user_id']}")
    
    return result

# ==================== HEALTH CHECK ====================
@api_router.get("/")
async def root():
    return {"message": "MatchMe API", "status": "healthy"}

@api_router.get("/health")
async def health():
    return {"status": "ok"}

# Include the router in the main app
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[os.environ.get('FRONTEND_URL', 'http://localhost:3000')],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== STARTUP ====================
@app.on_event("startup")
async def startup():
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("user_id", unique=True)
    await db.photos.create_index("user_id")
    await db.photos.create_index("photo_id", unique=True)
    await db.jobs.create_index("user_id")
    await db.jobs.create_index("job_id", unique=True)
    await db.ratings.create_index([("rater_id", 1), ("photo_id", 1)], unique=True)
    await db.login_attempts.create_index("identifier")
    
    # Initialize storage
    try:
        init_storage()
        logger.info("Storage initialized")
    except Exception as e:
        logger.error(f"Storage init failed: {e}")
    
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
            "ratings_given": 0,
            "ratings_earned": 0,
            "onboarding_completed": True,
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Admin user created: {admin_email}")
    elif not verify_password(admin_password, existing.get("password_hash", "")):
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"password_hash": hash_password(admin_password)}}
        )
        logger.info("Admin password updated")
    
    # Write test credentials
    os.makedirs("/app/memory", exist_ok=True)
    with open("/app/memory/test_credentials.md", "w") as f:
        f.write(f"""# Test Credentials

## Admin Account
- Email: {admin_email}
- Password: {admin_password}
- Role: admin

## Test User
- Register with any email to create a test user
- Default credits: 3

## Auth Endpoints
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/me
- POST /api/auth/refresh
- POST /api/auth/google/session
""")
    logger.info("Test credentials written")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
