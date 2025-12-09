# Gym Habit - Partner Gym Finder
**Habit Health by HCL Healthcare**

A web application that helps users discover partner gym memberships. Users can filter by brand, find nearby locations using geolocation, view details, and submit subscription interest forms.

---

## Features

- **Brand Filtering:** Select from top gym partners (Cult, Gold's Gym, Anytime Fitness, Talwalkar's, Fitness First)
- **Location-Based Search:** Find nearest gyms using device geolocation (Haversine distance calculation)
- **Gym Details:** View comprehensive information including amenities, pricing plans with discounts
- **Subscription Inquiry:** Submit interest form with user details
- **Admin Panel:** Manage gym database and view subscription requests
- **Fast Performance:** All data loaded in memory for sub-100ms response times

---

## Tech Stack

**Backend:**
- Python 3.8+
- FastAPI (modern, fast web framework)
- Uvicorn (ASGI server)
- CSV-based data storage (in-memory loading)

**Frontend:**
- HTML5 + CSS3 + Vanilla JavaScript
- No frameworks or dependencies
- Responsive design (mobile-first)
- "Healthcare Energy" design theme (light background + Cult Fit-inspired gradients)

**Deployment Target:**
- AWS EC2 (t2.micro)
- Ubuntu/Amazon Linux
- Cost: ~$8-10/month for 1,000-2,000 users

---

## Project Structure

```
gym_habit/
├── main.py                    # FastAPI backend server
├── database.py                # CSV operations & Haversine distance calculation
├── requirements.txt           # Python dependencies
├── gyms.csv                   # Gym database (30 sample gyms included)
├── subscription_requests.json # Auto-generated when users submit forms
├── frontend/
│   ├── index.html             # Main user page
│   ├── admin.html             # Admin panel
│   ├── style.css              # Unified stylesheet
│   └── assets/                # Images (if any)
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
└── DEPLOYMENT_GUIDE.md        # AWS deployment instructions
```

---

## Quick Start - Local Setup

### 1. Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### 2. Install Dependencies

```bash
cd gym_habit
pip install -r requirements.txt
```

**Dependencies:**
- fastapi==0.104.1
- uvicorn[standard]==0.24.0
- python-multipart==0.0.6
- pydantic[email]==2.5.0

### 3. Run the Server

```bash
python main.py
```

**Server will start on:** `http://localhost:8000`

You should see:
```
============================================================
GYM HABIT - Habit Health Partner Gym Finder
============================================================
[OK] Loaded 30 gyms from database
[OK] Available partners: 5
[ADMIN] Admin password: habitadmin2025
============================================================
[STARTING] Starting server...
[INFO] Main page: http://localhost:8000
[INFO] Admin panel: http://localhost:8000/admin
[INFO] API docs: http://localhost:8000/docs
============================================================
```

### 4. Access the Application

- **Main Page:** http://localhost:8000
- **Admin Panel:** http://localhost:8000/admin
- **API Documentation:** http://localhost:8000/docs

---

## User Guide

### Finding Gyms

1. Open http://localhost:8000
2. **Select a gym partner** (e.g., "Cult")
3. Browse all gyms OR click **"Find Nearby Gyms"**
   - Browser will request location permission
   - Allow to see gyms sorted by distance
4. **Click on a gym card** to view details
5. **Fill the subscription form** to submit interest

### Form Fields
- Full Name (required)
- Email (required)
- Phone (10-digit Indian mobile, required)
- Preferred Plan (1-month, 3-month, or 12-month)
- Message (optional)

### Success
After submission, you'll see: *"Thank you! Our wellness team will contact you within 24 hours to help you start your fitness journey."*

---

## Admin Guide

### Accessing Admin Panel

1. Navigate to http://localhost:8000/admin
2. Enter password: **habitadmin2025**
3. Click "Login to Admin Panel"

### Admin Features

**Dashboard Stats:**
- Total Gyms count
- Total Partners count
- Total Subscription Requests count

**Manage Gyms Tab:**
- View all gyms in table
- **Add New Gym:** Click "+ Add New Gym" button, fill form
- **Delete Gym:** Click "Delete" button, confirm

**View Subscriptions Tab:**
- See all user requests
- Contact information (phone, email)
- Gym selected and preferred plan

**Upload CSV Tab:**
- Replace entire gym database
- Click area to select CSV file
- **Warning:** This replaces ALL existing gyms (backup created automatically)

### CSV Format

Your CSV must have these exact columns:
```
PartnerName,GymName,Address,Pincode,Latitude,Longitude,SubscriptionAmount,Amenities
```

**Example Row:**
```csv
Cult,Cult Fit Andheri West,Veera Desai Road Andheri West Mumbai,400053,19.1350,72.8352,2499,"Cardio Zone,Weight Training,Yoga Studio"
```

**Rules:**
- PartnerName: Gym brand (e.g., "Cult", "Gold's Gym")
- GymName: Full gym name with location
- Address: Complete address
- Pincode: 6-digit Indian pincode
- Latitude/Longitude: Decimal degrees (e.g., 19.1350, 72.8352)
- SubscriptionAmount: Monthly price in INR (e.g., 2499)
- Amenities: Comma-separated list in quotes

---

## API Endpoints

### Public Endpoints

**GET /api/partners**
- Get list of all gym partners
- Response: `{"partners": [{"name": "Cult", "count": 10}], "total": 5}`

**GET /api/gyms?partner={name}**
- Get gyms filtered by partner (optional)
- Example: `/api/gyms?partner=Cult`

**GET /api/gyms/nearby?lat={lat}&lon={lon}&partner={name}&limit={limit}**
- Find nearest gyms
- Example: `/api/gyms/nearby?lat=19.1136&lon=72.8697&partner=Cult&limit=10`

**GET /api/gyms/{gym_id}**
- Get gym details with subscription plans

**POST /api/subscription/request**
- Submit subscription inquiry

### Admin Endpoints (Password Required)

**POST /api/admin/login**
- Authenticate admin

**GET /api/admin/gyms?password={password}**
- Get all gyms

**POST /api/admin/gyms/add?password={password}**
- Add new gym

**DELETE /api/admin/gyms/{gym_id}?password={password}**
- Delete gym

**POST /api/admin/gyms/upload-csv**
- Upload CSV file

**GET /api/admin/subscriptions?password={password}**
- Get all subscription requests

---

## Subscription Plans Calculation

Base monthly price stored in CSV is auto-calculated into 3 plans:

**Example:** Base price = ₹2,499/month

| Plan | Total | Per Month | Discount | Savings |
|------|-------|-----------|----------|---------|
| 1-month | ₹2,499 | ₹2,499 | 0% | ₹0 |
| 3-month | ₹6,972 | ₹2,324 | 7% | ₹524 |
| 12-month | ₹24,890 | ₹2,074 | 17% | ₹5,097 |

**Formula:**
- 1-month: base_price
- 3-month: base_price × 3 × 0.93 (7% discount)
- 12-month: base_price × 12 × 0.83 (17% discount)

---

## Haversine Distance Calculation

The app uses the Haversine formula to calculate great-circle distances between coordinates (accurate to ~0.5%):

```python
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)² + cos(lat1) * cos(lat2) * sin(dlon/2)²
    c = 2 * arcsin(sqrt(a))
    distance = R * c
    return round(distance, 2)
```

---

## Sample Data

The project includes **30 sample gyms**:
- 6 Cult gyms (Mumbai, Bangalore)
- 6 Gold's Gym locations (Mumbai, Delhi)
- 6 Anytime Fitness gyms (Mumbai, Pune, Bangalore, Gurgaon)
- 6 Talwalkar's gyms (Mumbai, Pune, Nagpur, Surat)
- 6 Fitness First gyms (Mumbai, Bangalore, Gurgaon, Noida, Chennai)

---

## Troubleshooting

**Issue:** Server won't start
- **Solution:** Check if port 8000 is available. Change port in `main.py` if needed.

**Issue:** "CSV file not found"
- **Solution:** Ensure `gyms.csv` exists in the project root directory.

**Issue:** Location access denied
- **Solution:** User needs to enable location permissions in browser settings.

**Issue:** No gyms showing after selecting brand
- **Solution:** Check if CSV has gyms for that partner. Check console for errors.

**Issue:** Form submission fails
- **Solution:** Check network connection. Check browser console for errors.

**Issue:** Admin password not working
- **Solution:** Default password is `habitadmin2025`. Check `main.py` line 42.

---

## Development

### Running in Development Mode

Server auto-reloads on file changes:
```bash
python main.py
```

### Running Tests

Test database module:
```bash
python database.py
```

Test specific API endpoint:
```bash
curl http://localhost:8000/api/partners
```

### Modifying Design

Edit `frontend/style.css` to change colors, fonts, or layout.

**Current Design System:**
- Primary color: Teal (#14b8a6) - healthcare trust
- Accent: Gold-to-Pink gradient (#FFDB17 → #FF3278) - fitness energy
- Background: Light gradient (white → soft teal)
- Font: Inter (Google Fonts)

---

## Performance

**Expected Performance:**
- Page load: <2 seconds
- Gym search: <200ms (in-memory)
- Distance calculation (10 gyms): <50ms
- Form submission: <300ms

**Scalability:**
- Current: Handles 10,000 gyms with ~3MB RAM
- Supports 100+ concurrent users on t2.micro
- For 100,000+ gyms, migrate to PostgreSQL

---

## Security

**Current Setup (Development/MVP):**
- Simple password authentication for admin
- CORS enabled for all origins
- Input validation on all forms
- XSS protection via HTML escaping

**Production Recommendations:**
- Use environment variables for admin password
- Restrict CORS to specific domain
- Add rate limiting (slowapi)
- Use HTTPS (Let's Encrypt)
- Consider JWT authentication for admin

---

## Next Steps (Future Enhancements)

**Phase 2 Features:**
- Email confirmation on form submission (SendGrid/AWS SES)
- SMS to customer support on new requests (Twilio)
- Search by gym name or pincode
- Filter by amenities (checkboxes)
- Price range slider
- Gym ratings and reviews
- Export subscriptions to CSV
- Mark requests as "contacted/closed"
- Analytics dashboard (Google Analytics)
- Multi-language support

**Technical Upgrades:**
- Migrate to PostgreSQL for 100,000+ gyms
- Add Redis caching
- Implement CI/CD (GitHub Actions)
- Docker containerization
- JWT authentication for admin
- Automated testing (pytest)

---

## Support

For technical issues or questions:
1. Check this README
2. Check API documentation at `/docs`
3. Check `DEPLOYMENT_GUIDE.md` for AWS deployment
4. Review project files and code comments

---

## License

Proprietary - Habit Health by HCL Healthcare

---

## Credits

**Built for:** Habit Health (HCL Healthcare)
**Design Inspiration:** Cult Fit Aurora Design System
**Tech Stack:** FastAPI + Vanilla JavaScript
**Version:** 1.0.0
**Last Updated:** December 9, 2025

---

**Ready to deploy? See `DEPLOYMENT_GUIDE.md` for AWS EC2 deployment instructions.**
