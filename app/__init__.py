# app/__init__.py
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from mongoengine import connect
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 1. Enable CORS
    CORS(app)

    # 2. Initialize JWT Authentication
    jwt = JWTManager(app)

    # 3. Initialize MongoEngine Database Connection
    connect(host=app.config['MONGO_URI'])

    # 4. Auto-bootstrap initial Super Admin and default accounts if not present
    try:
        from models import User
        from werkzeug.security import generate_password_hash
        
        default_accounts = [
            {
                "name": "Super Administrator",
                "email": "superadmin@crm.com",
                "password": "admin123",
                "role": "Super Admin",
                "phoneNumber": "+1 800 555 0199"
            },
            {
                "name": "System Administrator",
                "email": "admin@crm.com",
                "password": "admin123",
                "role": "Admin",
                "phoneNumber": "+1 800 555 0198"
            },
            {
                "name": "John Sales",
                "email": "john.sales@crm.com",
                "password": "sales123",
                "role": "Sales Employee",
                "phoneNumber": "+1 800 555 0197"
            }
        ]

        for acc in default_accounts:
            if not User.objects(email=acc["email"]).first():
                User(
                    name=acc["name"],
                    email=acc["email"],
                    password=generate_password_hash(acc["password"]),
                    role=acc["role"],
                    phoneNumber=acc["phoneNumber"],
                    isActive=True
                ).save()
                print(f"Auto-bootstrapped default account: {acc['email']}")

        # Ensure default CMS page contents exist
        from app.cms.controllers import seed_cms_defaults_if_needed
        seed_cms_defaults_if_needed()
    except Exception as e:
        print("Auto-bootstrap notice:", e)

    # 5. ---------------- Register API Blueprints ----------------

    from app.auth import authBp
    app.register_blueprint(authBp, url_prefix='/api/auth')

    from app.users import usersBp
    app.register_blueprint(usersBp, url_prefix='/api/users')

    from app.leads import leadsBp
    app.register_blueprint(leadsBp, url_prefix='/api/leads')

    from app.projects import projectsBp
    app.register_blueprint(projectsBp, url_prefix='/api/projects')

    from app.buildings import buildingsBp
    app.register_blueprint(buildingsBp, url_prefix='/api/buildings')

    from app.units import unitsBp
    app.register_blueprint(unitsBp, url_prefix='/api/units')

    from app.bookings import bookingsBp
    app.register_blueprint(bookingsBp, url_prefix='/api/bookings')

    from app.dashboard import dashboardBp
    app.register_blueprint(dashboardBp, url_prefix='/api/dashboard')

    from app.cms import cmsBp
    app.register_blueprint(cmsBp, url_prefix='/api/cms')

    from app.notifications import notificationsBp
    app.register_blueprint(notificationsBp, url_prefix='/api/notifications')

    # 6. ---------------- Register Web Frontend Blueprint ----------------
    from app.main import main_bp
    app.register_blueprint(main_bp, url_prefix='/')

    # ---------------- Health Check Route ----------------
    @app.route("/api/health", methods=["GET"])
    def health():
        return {
            "status": "success",
            "message": "Real Estate CRM API is operational"
        }

    return app