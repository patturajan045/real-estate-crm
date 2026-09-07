# EstateFlow - Real Estate CRM Application

A professional, modular Real Estate CRM built with **Python Flask**, **MongoDB (MongoEngine)**, **JWT Authentication**, and a clean light-themed frontend utilizing **Bootstrap 5**, **jQuery DataTables**, and **SweetAlert2**.

---

## 🌟 Key Features

1. **Role-Based Access Control (RBAC)**:
   - **Super Admin**: Full authority over team users, inventory, leads, bookings, and dashboard analytics.
   - **Admin**: Manage inventory, leads, assign leads, review bookings, and monitor analytics.
   - **Sales Employee**: Manage assigned leads, log call activities/notes, schedule follow-ups, check live unit availability, and execute bookings.

2. **Lead Pipeline Management**:
   - Stages: **New**, **Contacted**, **Site Visit**, **Interested**, **Negotiation**, **Booked**, **Lost**.
   - Interactive stage filter pills with live counts.
   - Search leads by customer name, phone, email, and city.
   - Activity timeline with history of notes, author stamps, and next follow-up dates.
   - Direct 1-click conversion from lead to booking.

3. **Property & Inventory Management**:
   - Hierarchical structure: **Projects** &rarr; **Buildings / Towers** &rarr; **Units**.
   - Unit parameters: Unit number, floor, type (`1BHK`, `2BHK`, `3BHK`, `4BHK`, `Penthouse`, `Villa`, `Commercial`), carpet area (sq ft), price ($), and status.
   - Availability statuses: `Available` (Green), `Blocked` (Amber), `Booked` (Red), `Sold` (Dark Gray).
   - Real-time unit availability filtering and quick "Book Unit" triggers.

4. **Booking System & Concurrency Protection**:
   - Connects a customer lead to an available property unit.
   - **Atomic MongoDB Check-and-Set**: Prevents two sales employees from double-booking the same unit.
   - SweetAlert2 concurrency guard alerting users immediately if a unit was just claimed.
   - Booking cancellation workflow with reason tracking and atomic return of unit to the available pool.

5. **Sales & Analytics Dashboard**:
   - Real-time KPIs: Total Leads, Pending Follow-ups (Today / Overdue), Available Units, Confirmed Revenue ($), Total Bookings.
   - Chart.js Pipeline visualization (Leads by Stage).
   - Chart.js Inventory Distribution donut chart.
   - Pending follow-up alerts table with 1-click note logger.
   - Recent bookings log.

6. **Reusable Architecture (Low-Code / Scalable)**:
   - Centralized API client (`crm-app.js`) handling JWT attachment, 401 redirection, and error handling.
   - SweetAlert2 popups (`CRM.alert`, `CRM.success`, `CRM.error`, `CRM.confirm`, `CRM.toast`).
   - Dynamic jQuery DataTables standardizer.
   - Dynamic form serializers and data binders.

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.10+
- MongoDB 6.0+ (running locally on `mongodb://localhost:27017`)

### 2. Environment Setup
```bash
# Virtual environment is already prepared in .venv
# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Or run with the virtualenv python directly:
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Automatic Database Bootstrapping (Zero seed.py Needed)
EstateFlow eliminates the need for manual seed scripts. When launched against an empty database, the application automatically initializes the default Super Administrator account and all dynamic CMS page content keys. All properties, leads, and bookings are created and managed dynamically through the web interface and REST APIs.

### 4. Run the Application
```bash
# Development (Flask built-in server)
.\.venv\Scripts\python.exe run.py

# Production on Windows (Waitress WSGI)
waitress-serve --port=5000 run:app

# Production on Linux / Cloud (Gunicorn)
gunicorn --bind 0.0.0.0:5000 run:app
```
Open your browser and navigate to:
```
http://localhost:5000/
```

---

## 🔑 Default Login Credentials (Login by Email OR Username)

Users can sign in using either their **Email Address** OR their **Username / Full Name** (case-insensitive):

| Role | Email | Username | Password | Permissions |
|---|---|---|---|---|
| **Super Admin** | `superadmin@crm.com` | `Super Administrator` | `admin123` | Full control, Team management, **Exclusive Platform Settings (CMS)** |
| **Admin** | `admin@crm.com` | `System Administrator` | `admin123` | Inventory, Leads, Bookings, Team management, Analytics |
| **Sales Employee** | `john.sales@crm.com` | `John Sales` | `sales123` | Assigned leads, Bookings, Availability, Follow-ups |

---

## 📁 Project Structure

```
d:/real_estate_crm/
├── app/
│   ├── __init__.py          # Flask app factory, Blueprint registration, CORS & JWT setup
│   ├── config.py            # Environment configuration, JWT key, Mongo URI
│   ├── cms/                 # Dynamic Page Content CMS module (MongoDB-backed)
│   │   ├── __init__.py
│   │   ├── routes.py        # /api/cms/content, /batch, /reset
│   │   └── controllers.py   # CMS REST controllers
│   ├── auth/                # Authentication endpoints (login, register, logout, me)
│   ├── users/               # Team user CRUD and role management
│   ├── leads/               # Lead management, stages, notes, and search
│   ├── projects/            # Real estate projects
│   ├── buildings/           # Buildings & towers
│   ├── units/               # Inventory units and status
│   ├── bookings/            # Concurrency-safe atomic booking system
│   ├── dashboard/           # Real-time analytics, pipeline charts, and urgent follow-ups
│   ├── main/                # Web frontend template router
│   ├── static/
│   │   ├── css/style.css    # Professional light theme stylesheet (Outline buttons, DataTables)
│   │   └── js/              # Modular JavaScript Architecture (Zero inline scripts in HTML)
│   │       ├── crm-app.js   # Core client, JWT handler, SweetAlert2, DataTables, CMS loader
│   │       ├── auth.js      # Login and Register form handling
│   │       ├── dashboard.js # Real-time dashboard KPI & Chart.js rendering
│   │       ├── leads.js     # Lead management, stage filter pills, notes timeline
│   │       ├── properties.js# Units, Projects, and Buildings inventory management
│   │       ├── bookings.js  # Booking wizard, atomic race condition alert, cancellation
│   │       ├── users.js     # User administration & role management
│   │       └── settings.js  # Super Admin & Admin dynamic CMS page content editor
│   └── templates/           # Clean HTML templates (ZERO inline <script> code)
│       ├── base.html        # Shared layout, left-aligned toggle, dynamic navigation CMS
│       ├── login.html       # Clean authentication portal with eye toggle
│       ├── register.html    # Self-service user registration
│       ├── settings.html    # Super Admin & Admin Platform Content Settings editor
│       ├── dashboard.html   # Sales dashboard
│       ├── leads.html       # Full lead management
│       ├── properties.html  # Inventory tab view (Units, Projects, Buildings)
│       ├── bookings.html    # Booking management
│       └── users.html       # User & role administration
├── db.py                    # PyMongo database connection
├── models.py                # MongoEngine schemas (User, PageContent, Project, Building, Unit, Lead, Booking)
├── requirements.txt         # Dependencies (Flask, mongoengine, Flask-JWT-Extended, reportlab)
├── run.py                   # Development entry point
├── generate_user_guide_pdf.py # Generates comprehensive 9-page User Guide PDF
├── EstateFlow_CRM_User_Guide.pdf # Publication-ready User Manual & Operations Guide
├── test_crm.py              # Comprehensive production test suite (Health, Auth, RBAC, Inventory, Bookings)
├── .env.example             # Environment variables template for deployment
└── .gitignore               # Comprehensive Git ignore rules (Python, venv, secrets, logs)
```

---

## 🧪 Running Automated Tests

Run the comprehensive production test suite:

```bash
.\.venv\Scripts\python.exe test_crm.py
```

All 34 automated integration tests verify:
1. Dynamic UI text key retrieval and grouped hierarchy from MongoDB
2. Batch update and reset of dynamic headings/paragraphs
3. User self-registration defaulting to Sales Employee
4. Zero inline `<script>` tags across all 9 HTML templates
5. Zero `placeholder` attributes across all HTML input forms (clean icon-only inputs)
6. Interactive password show/hide eye toggle functionality
7. Responsive collapsible icon-only sidebar with persistent state
8. Custom professional jQuery DataTables styling
9. Complete sanitization of technical jargon from user-facing UI and SweetAlert2
10. Robust Add, Edit, Delete, Update CRUD operations across Projects, Buildings, Units, and Leads
11. Atomic double-booking concurrency prevention and booking cancellation release
