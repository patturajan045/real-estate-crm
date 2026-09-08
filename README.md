# Real Estate CRM Application

A high-performance, modular Real Estate CRM built for modern property sales teams with **Python Flask**, **MongoDB (MongoEngine)**, **JWT Authentication**, and a clean light-themed responsive frontend utilizing **Bootstrap 5**, **jQuery DataTables**, and **SweetAlert2**.

---

## 🌟 Key Features

1. **Role-Based Access Control (RBAC)**:
   - **Super Admin**: Full authority over team users, platform branding/CMS copy, inventory, leads, bookings, and dashboard analytics.
   - **Admin**: Operational management of inventory, leads, team members, booking agreements, and sales analytics.
   - **Sales Employee**: Manage assigned leads, record call activities & notes, schedule follow-ups, inspect live unit inventory, and execute booking agreements.

2. **Lead Pipeline Management**:
   - 7 Progressive Stages: **New**, **Contacted**, **Site Visit**, **Interested**, **Negotiation**, **Booked**, **Lost**.
   - Interactive stage filter pills with live counters.
   - Instant search across customer name, phone, email, and city.
   - Activity timeline tracking notes history, author stamps, and next follow-up dates.
   - Direct 1-click conversion from lead to property booking.

3. **Property & Inventory Directory**:
   - 3-tier hierarchy: **Projects** &rarr; **Buildings / Towers** &rarr; **Units**.
   - Comprehensive unit specs: Unit number, floor, unit type (`1BHK`, `2BHK`, `3BHK`, `4BHK`, `Penthouse`, `Villa`, `Commercial`), carpet area (sq ft), price ($), and status.
   - Live availability tracking: `Available` (Green), `Blocked` (Amber), `Booked` (Red), `Sold` (Dark Gray).

4. **Atomic Booking Engine & Concurrency Guard**:
   - Connects a customer lead to an available property unit with agreement value, booking deposit, and payment tracking.
   - **Atomic MongoDB Check-and-Set**: Prevents two sales employees from double-booking the same unit simultaneously.
   - Immediate SweetAlert2 alerts if a unit was just reserved by another agent.
   - Cancellation workflow with reason tracking and atomic return of units to the available pool.

5. **In-App Follow-up & Assignment Notification Center**:
   - Topbar notification bell with unread badge counter and real-time polling.
   - Automated notifications whenever leads or booking follow-ups are assigned, specifying the manager/assigner name.
   - Quick "Mark Read" and "Mark All Read" actions with toast alerts.

6. **Executive Sales & Analytics Dashboard**:
   - Real-time KPIs: Total Leads, Pending Follow-ups (Today / Overdue), Available Units, Confirmed Revenue ($), Total Bookings.
   - Interactive Chart.js Pipeline visualization (Leads by Stage) and Inventory Distribution donut chart.
   - Urgent follow-ups table with 1-click note logging modal.
   - Recent bookings log with customer, unit, and agent references.

---

## 🧠 Important Architectural & Engineering Decisions

When building for a real sales team with edge cases, data consistency, and practical workflows in mind, the following 5 key decisions were made:

### 1. Atomic MongoDB Check-and-Set Concurrency Guard for Bookings (Data Consistency)
- **The Challenge**: In high-demand real estate sales, multiple agents may pitch the same popular unit and attempt to finalize a reservation simultaneously. Standard read-then-write logic creates race conditions where two agents generate conflicting agreements for the same unit.
- **Decision & Rationale**: We implemented an atomic conditional update:
  ```python
  updated_count = Unit.objects(id=unit_id, status=Unit.STATUS_AVAILABLE).update_one(set__status=Unit.STATUS_BOOKED)
  if updated_count == 0:
      return jsonify({"status": "error", "message": "Double booking prevented! Unit is no longer available."}), 409
  ```
  Combined with a unique partial index on confirmed unit bookings, this eliminates double-booking risks at the database level. If a booking is cancelled, the unit status automatically reverts to `Available`.

### 2. Deactivation-First User Lifecycle with Lead Safety Guard (Data Protection)
- **The Challenge**: Deleting a sales agent who owns active pipeline leads or historical client agreements can cause orphaned records, broken foreign keys, or missing customer follow-ups.
- **Decision & Rationale**: We enforced a two-stage safety policy:
  1. Active team members cannot be permanently deleted directly—they must be deactivated first (`isActive = False`), preventing accidental staff removal while immediately disabling login access.
  2. When an inactive staff member is permanently deleted, the system executes `Lead.objects(assignedTo=user.id).update(set__assignedTo=None)` to safely return leads to the unassigned pool rather than deleting customer relationships or leaving dangling references. Self-deletion of the active logged-in user is strictly blocked.

### 3. In-App Notification Center for Follow-Up Assignments (Sales Team Productivity)
- **The Challenge**: In a fast-paced sales team, leads and follow-up dates assigned by managers often get lost if agents must manually reload and filter tables.
- **Decision & Rationale**: Built a persistent notification system backed by a MongoDB `Notification` collection with topbar badge counters and 30-second polling. Whenever a lead is assigned or a follow-up date is scheduled/updated, an automatic notification is created explicitly naming the assigner (`"Follow-up assigned by [Assigner Name] for [Customer Name]"`). Agents see immediate toast notifications upon login or action, keeping pipeline tasks front-and-center.

### 4. Hierarchical RBAC with Super Admin Exclusive Platform Settings (Permissions Integrity)
- **The Challenge**: While regular Admins need operational authority to manage inventory, leads, and staff accounts, allowing them to modify system-wide dynamic copy, branding, or CMS settings could disrupt operations or brand consistency.
- **Decision & Rationale**: Enforced strict privilege separation:
  - **Super Admin**: Exclusively authorized to access `/settings` and mutate CMS copy (`check_super_admin_access()` returns HTTP 403 Forbidden for all other roles).
  - **Admin**: Full operational control over inventory, team, leads, and bookings without access to platform branding.
  - **Sales Employee**: Focused strictly on customer relationships, follow-ups, and unit reservations.

### 5. Universal Dual Login (Email OR Username) with Case-Insensitive Matching (User Experience)
- **The Challenge**: Sales reps frequently identify teammates or log into CRM systems using their username/full name rather than a long corporate email address. Strict browser email validation rules reject non-email formats.
- **Decision & Rationale**: Updated `/api/auth/login` to accept either email or username. The backend matches against `email__iexact` first, then falls back to `name__iexact` (case-insensitive). The frontend input uses `type="text"` with `autocomplete="username"` so agents can seamlessly sign in with either credential.

---

## 🚀 Setup & Installation Instructions

### 1. Prerequisites
- **Python**: Version 3.10, 3.11, 3.12, 3.13, or 3.14
- **MongoDB**: Version 6.0+ running locally on `localhost:27017` or a MongoDB Atlas cluster URI
- **Git** (optional, for version control)

### 2. Clone or Extract Project
Navigate to the project root directory:
```bash
cd d:\real_estate_crm
```

### 3. Create & Activate Virtual Environment
```bash
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy the provided `.env.example` template to `.env`:
```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```
Default `.env` configuration:
```env
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=estateflow_super_secure_key_2026
JWT_SECRET_KEY=estateflow_jwt_secret_key_2026_secure
MONGO_URI=mongodb://localhost:27017/real_estate_crm
PORT=5000
```
> **Note**: For cloud deployments (MongoDB Atlas), replace `MONGO_URI` with your cluster connection string (e.g. `mongodb+srv://<user>:<password>@cluster0.mongodb.net/real_estate_crm?retryWrites=true&w=majority`).

### 6. Automatic First-Run Bootstrapping (Zero `seed.py` Required)
EstateFlow eliminates the need for manual seed scripts. When launched against an empty database, the application automatically:
- Creates the default Super Administrator, Admin, and Sales Employee accounts with secure password hashing.
- Initializes all 48 canonical dynamic CMS page copy keys in MongoDB.
- Pure database flow: all future projects, units, leads, and bookings are created dynamically through the UI and REST APIs.

### 7. Run the Application

#### Option A: Local Development (Built-in Flask Server)
```bash
python run.py
```

#### Option B: Production Deployment on Windows (Waitress WSGI)
```bash
waitress-serve --port=5000 run:app
```

#### Option C: Production Deployment on Linux / Cloud (Gunicorn)
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 run:app
```

Navigate to:
```
http://localhost:5000/
```

---

## 🔑 Default Login Credentials

Users can log in using either their **Email Address** OR their **Username / Full Name** (case-insensitive):

| Role | Email | Username | Password | Access Scope |
|---|---|---|---|---|
| **Super Admin** | `superadmin@crm.com` | `Super Administrator` | `admin123` | Full system control, Team management, **Exclusive Platform Settings (CMS)** |
| **Admin** | `admin@crm.com` | `System Administrator` | `admin123` | Inventory, Leads, Bookings, Team management, Sales Analytics |
| **Sales Employee** | `john.sales@crm.com` | `John Sales` | `sales123` | Assigned leads, Bookings, Availability, Follow-up notes |

---

## 📁 Project Structure

```
d:/real_estate_crm/
├── app/
│   ├── __init__.py          # Flask app factory, Blueprint registration, CORS & JWT setup
│   ├── config.py            # Environment configuration, load_dotenv, JWT key, Mongo URI
│   ├── cms/                 # Dynamic Page Content CMS module (MongoDB-backed)
│   │   ├── __init__.py
│   │   ├── routes.py        # /api/cms/content, /batch, /reset
│   │   └── controllers.py   # CMS REST controllers & Super Admin authorization
│   ├── auth/                # Authentication endpoints (login, register, logout, me)
│   ├── users/               # Team user CRUD, deactivation, and inactive user deletion
│   ├── leads/               # Lead management, pipeline stages, notes, and search
│   ├── projects/            # Real estate projects
│   ├── buildings/           # Buildings & towers
│   ├── units/               # Inventory units and live status
│   ├── bookings/            # Concurrency-safe atomic booking system
│   ├── notifications/       # In-app notification center (follow-up & booking alerts)
│   ├── dashboard/           # Real-time analytics, pipeline charts, and urgent follow-ups
│   ├── main/                # Web frontend template router
│   ├── static/
│   │   ├── css/style.css    # Professional light theme stylesheet (Outline buttons, DataTables)
│   │   └── js/              # Modular JavaScript Architecture (Zero inline scripts in HTML)
│   │       ├── crm-app.js   # Core client, JWT handler, SweetAlert2, DataTables, Notifications
│   │       ├── auth.js      # Login and Register form handling
│   │       ├── dashboard.js # Real-time dashboard KPI & Chart.js rendering
│   │       ├── leads.js     # Lead management, stage filter pills, notes timeline
│   │       ├── properties.js# Units, Projects, and Buildings inventory management
│   │       ├── bookings.js  # Booking wizard, atomic race condition alert, cancellation
│   │       ├── users.js     # User administration & role management
│   │       └── settings.js  # Super Admin dynamic CMS page content editor
│   └── templates/           # Clean HTML templates (ZERO inline <script> code)
│       ├── base.html        # Shared layout, left-aligned toggle, dynamic navigation CMS
│       ├── login.html       # Clean authentication portal with eye toggle
│       ├── register.html    # Self-service user registration
│       ├── settings.html    # Super Admin Platform Content Settings editor
│       ├── dashboard.html   # Sales dashboard
│       ├── leads.html       # Full lead management
│       ├── properties.html  # Inventory tab view (Units, Projects, Buildings)
│       ├── bookings.html    # Booking management
│       └── users.html       # User & role administration
├── db.py                    # PyMongo database connection
├── models.py                # MongoEngine schemas (User, PageContent, Project, Building, Unit, Lead, Booking, Notification)
├── requirements.txt         # Dependencies (Flask, mongoengine, Flask-JWT-Extended, gunicorn, waitress, reportlab)
├── run.py                   # WSGI application entry point
├── generate_user_guide_pdf.py # Script generating comprehensive 9-page User Guide PDF
├── EstateFlow_CRM_User_Guide.pdf # Publication-ready User Manual & Operations Guide
├── test_crm.py              # Comprehensive production test suite (Health, Auth, RBAC, Inventory, Bookings)
├── .env.example             # Environment variables template for deployment
└── .gitignore               # Comprehensive Git ignore rules (Python, venv, secrets, logs)
```

---

## 🧪 Running Automated Tests

Execute the comprehensive automated production test suite:

```bash
.\.venv\Scripts\python.exe test_crm.py
```

All test cases verify:
1. System Health Check & Database Connectivity
2. Authentication via Email AND Username (Case-Insensitive)
3. Role-Based Access Control & Super Admin Platform Settings Exclusivity (HTTP 403 Forbidden for Admin)
4. User Deactivation & Inactive User Deletion with Lead Unassignment Safety Guard
5. In-App Notifications for Lead Assignment and Booking Follow-up
6. Complete Project, Building, and Unit Inventory Management
7. Lead Pipeline Operations & Follow-up Scheduling
8. Atomic Double-Booking Prevention & Reservation Lifecycle
9. Dynamic CMS Headings and Labels
10. All 9 Frontend Template Routes Rendered with HTTP 200 OK
