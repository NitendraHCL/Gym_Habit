"""
Gym Habit - FastAPI Backend Server
Habit Health by HCL Healthcare
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Query, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
import uvicorn
import shutil
from pathlib import Path

from database import GymDatabase, SubscriptionManager, calculate_subscription_plans

# Initialize FastAPI app
app = FastAPI(
    title="Gym Habit API",
    description="Partner Gym Finder for Habit Health",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: ["https://habithealth.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and subscription manager
db = GymDatabase("gyms.csv")
sub_manager = SubscriptionManager("subscription_requests.json")

# Admin password (in production: use environment variable)
ADMIN_PASSWORD = "habitadmin2025"

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")


# ============================================================================
# PYDANTIC MODELS FOR REQUEST VALIDATION
# ============================================================================

class SubscriptionRequest(BaseModel):
    """Subscription form data"""
    gym_id: int
    gym_name: str
    partner_name: str
    full_name: str
    email: EmailStr
    phone: str
    preferred_plan: str
    billing_address: str
    message: Optional[str] = ""
    user_latitude: Optional[float] = None
    user_longitude: Optional[float] = None
    user_city: Optional[str] = None

    @validator('phone')
    def validate_phone(cls, v):
        """Validate 10-digit Indian phone number"""
        if not v.isdigit() or len(v) != 10:
            raise ValueError('Phone must be 10 digits')
        if not v[0] in '6789':
            raise ValueError('Phone must start with 6, 7, 8, or 9')
        return v

    @validator('full_name')
    def validate_name(cls, v):
        """Validate name length"""
        if len(v) < 3:
            raise ValueError('Name must be at least 3 characters')
        if len(v) > 100:
            raise ValueError('Name must be less than 100 characters')
        return v.strip()

    @validator('preferred_plan')
    def validate_plan(cls, v):
        """Validate plan selection"""
        valid_plans = ['1-month', '3-month', '12-month']
        if v not in valid_plans:
            raise ValueError(f'Plan must be one of: {valid_plans}')
        return v


class GymAddRequest(BaseModel):
    """Add gym request"""
    partner_name: str
    gym_name: str
    address: str
    pincode: str
    latitude: float
    longitude: float
    subscription_amount: int
    amenities: str

    @validator('pincode')
    def validate_pincode(cls, v):
        """Validate Indian pincode"""
        if not v.isdigit() or len(v) != 6:
            raise ValueError('Pincode must be 6 digits')
        return v

    @validator('latitude')
    def validate_latitude(cls, v):
        """Validate latitude range"""
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @validator('longitude')
    def validate_longitude(cls, v):
        """Validate longitude range"""
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v


# ============================================================================
# FRONTEND ROUTES
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve main user page"""
    try:
        return FileResponse("frontend/index.html")
    except:
        return HTMLResponse("<h1>Frontend not found. Please build frontend first.</h1>")


@app.get("/admin", response_class=HTMLResponse)
async def serve_admin():
    """Serve admin panel"""
    try:
        return FileResponse("frontend/admin.html")
    except:
        return HTMLResponse("<h1>Admin panel not found.</h1>")


# ============================================================================
# API ENDPOINTS - PUBLIC
# ============================================================================

@app.get("/api/partners")
async def get_partners():
    """
    Get list of all gym partners with counts
    Returns: {"partners": [{"name": "Cult", "count": 10}], "total": 5}
    """
    partners = db.get_all_partners()
    return {
        "partners": partners,
        "total": len(partners)
    }


@app.get("/api/gyms")
async def get_gyms(partner: Optional[str] = None):
    """
    Get all gyms, optionally filtered by partner
    Query params:
        partner (optional): Filter by partner name
    """
    if partner:
        gyms = db.get_gyms_by_partner(partner)
        return {
            "gyms": gyms,
            "total": len(gyms),
            "partner": partner
        }
    else:
        return {
            "gyms": db.gyms,
            "total": len(db.gyms)
        }


@app.get("/api/gyms/nearby")
async def get_nearby_gyms(
    lat: float = Query(..., description="User latitude"),
    lon: float = Query(..., description="User longitude"),
    partner: Optional[str] = Query(None, description="Filter by partner"),
    limit: int = Query(10, ge=1, le=50, description="Max results")
):
    """
    Find nearest gyms based on user location
    Query params:
        lat: User's latitude
        lon: User's longitude
        partner (optional): Filter by partner name
        limit (optional): Max number of results (default: 10)
    """
    gyms = db.get_nearby_gyms(lat, lon, partner, limit)

    return {
        "gyms": gyms,
        "total": len(gyms),
        "user_location": {"latitude": lat, "longitude": lon}
    }


@app.get("/api/gyms/{gym_id}")
async def get_gym_details(gym_id: int):
    """
    Get detailed information about a specific gym
    Path param:
        gym_id: Gym ID
    """
    gym = db.get_gym_by_id(gym_id)

    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")

    # Calculate subscription plans
    base_price = gym['subscription_amount']
    plans = calculate_subscription_plans(base_price)

    # Parse amenities
    amenities_list = [a.strip() for a in gym['amenities'].split(',')]

    response = gym.copy()
    response['subscription_plans'] = plans
    response['amenities_list'] = amenities_list

    return response


@app.post("/api/subscription/request")
async def submit_subscription_request(request: SubscriptionRequest):
    """
    Submit subscription inquiry form
    Body: SubscriptionRequest model
    """
    try:
        # Validate gym exists
        gym = db.get_gym_by_id(request.gym_id)
        if not gym:
            raise HTTPException(status_code=404, detail="Gym not found")

        # Save request
        request_id = sub_manager.save_request(request.dict())

        return {
            "success": True,
            "message": "Thank you! Our wellness team will contact you within 24 hours to help you start your fitness journey.",
            "request_id": request_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# API ENDPOINTS - ADMIN (Protected)
# ============================================================================

def verify_admin(password: str):
    """Verify admin password"""
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")


@app.post("/api/admin/login")
async def admin_login(password: str = Form(...)):
    """
    Admin login
    Form data:
        password: Admin password
    """
    verify_admin(password)
    return {"success": True, "message": "Login successful"}


@app.get("/api/admin/gyms")
async def admin_get_gyms(password: str = Query(...)):
    """
    Get all gyms (admin view)
    Query param:
        password: Admin password
    """
    verify_admin(password)

    return {
        "gyms": db.gyms,
        "total": len(db.gyms)
    }


@app.post("/api/admin/gyms/add")
async def admin_add_gym(
    password: str = Query(...),
    gym_data: GymAddRequest = None
):
    """
    Add new gym
    Query param:
        password: Admin password
    Body:
        GymAddRequest model
    """
    verify_admin(password)

    try:
        new_id = db.add_gym(gym_data.dict())
        return {
            "success": True,
            "gym_id": new_id,
            "message": "Gym added successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/admin/gyms/{gym_id}")
async def admin_delete_gym(
    gym_id: int,
    password: str = Query(...)
):
    """
    Delete gym
    Path param:
        gym_id: Gym ID
    Query param:
        password: Admin password
    """
    verify_admin(password)

    success = db.delete_gym(gym_id)

    if not success:
        raise HTTPException(status_code=404, detail="Gym not found")

    return {
        "success": True,
        "message": "Gym deleted successfully"
    }


@app.post("/api/admin/gyms/upload-csv")
async def admin_upload_csv(
    password: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Upload CSV to replace all gyms
    Form data:
        password: Admin password
        file: CSV file
    """
    verify_admin(password)

    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV")

    try:
        # Save uploaded file
        upload_path = "uploaded_gyms.csv"
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Replace gyms
        count = db.replace_all_gyms(upload_path)

        # Clean up
        Path(upload_path).unlink()

        return {
            "success": True,
            "gyms_loaded": count,
            "message": f"CSV uploaded successfully. {count} gyms loaded."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading CSV: {str(e)}")


@app.get("/api/admin/subscriptions")
async def admin_get_subscriptions(password: str = Query(...)):
    """
    Get all subscription requests
    Query param:
        password: Admin password
    """
    verify_admin(password)

    requests = sub_manager.get_all_requests()

    return {
        "requests": requests,
        "total": len(requests)
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "gyms_loaded": len(db.gyms),
        "partners": len(db.get_all_partners())
    }


# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("GYM HABIT - Habit Health Partner Gym Finder")
    print("=" * 60)
    print(f"[OK] Loaded {len(db.gyms)} gyms from database")
    print(f"[OK] Available partners: {len(db.get_all_partners())}")
    print(f"[ADMIN] Admin password: {ADMIN_PASSWORD}")
    print("=" * 60)
    print("[STARTING] Starting server...")
    print("[INFO] Main page: http://localhost:8000")
    print("[INFO] Admin panel: http://localhost:8000/admin")
    print("[INFO] API docs: http://localhost:8000/docs")
    print("=" * 60)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
