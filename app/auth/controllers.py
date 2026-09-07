from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User

def register():
    try:
        data = request.get_json(force=True) or {}

        # Validate fields
        if not data or not data.get("name") or not data.get("email") or not data.get("password"):
            return jsonify({
                "status": "error",
                "message": "Missing required fields (name, email, password)"
            }), 400

        # Check duplicate email
        if User.objects(email=data["email"].strip().lower()).first():
            return jsonify({
                "status": "error",
                "message": "Email already registered"
            }), 409

        # Assign roles based on the Real Estate CRM specifications
        email = data["email"].strip().lower()
        if "role" in data and data["role"] in User.ROLES:
            role = data["role"]
        elif email in ["patturajan045@gmail.com", "superadmin@crm.com"]:
            role = User.ROLE_SUPER_ADMIN
        elif email.startswith("admin"):
            role = User.ROLE_ADMIN
        else:
            role = User.ROLE_SALES

        # Create user
        user = User(
            name=data["name"].strip(),
            email=email,
            phoneNumber=data.get("phoneNumber", ""),
            password=generate_password_hash(data["password"]),
            role=role
        )
        user.save()

        # Generate JWT Token for immediate login after registration
        access_token = create_access_token(identity=str(user.id))

        return jsonify({
            "status": "success",
            "message": "Registered Successfully",
            "token": access_token,
            "user": {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "role": user.role
            }
        }), 201

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Server error: {str(e)}"
        }), 500


def login():
    try:
        data = request.get_json(force=True) or {}

        identifier = (data.get("email") or data.get("username") or data.get("login") or "").strip()
        password = data.get("password")

        if not identifier or not password:
            return jsonify({"status": "error", "message": "Email/Username and password are required"}), 400

        # Look up by email (case-insensitive) first, then fallback to name/username (case-insensitive)
        user = User.objects(email__iexact=identifier.lower()).first()
        if not user:
            user = User.objects(name__iexact=identifier).first()

        # Verify user exists and password matches
        if not user or not check_password_hash(user.password, password):
            return jsonify({"status": "error", "message": "Invalid email/username or password"}), 401

        # Check if the CRM account was deactivated
        if not user.isActive:
            return jsonify({"status": "error", "message": "Account is deactivated"}), 403

        # Generate JWT Token
        access_token = create_access_token(identity=str(user.id))

        return jsonify({
            "status": "success",
            "message": "Login successful",
            "token": access_token,
            "redirect": "/dashboard",
            "user": {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "role": user.role
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Server error: {str(e)}"
        }), 500


@jwt_required()
def logout():
    """
    JWT is stateless, meaning the token lives on the client (e.g., in localStorage).
    To 'log out', the frontend simply deletes the token.
    """
    return jsonify({
        "status": "success",
        "message": "Successfully logged out"
    }), 200


@jwt_required()
def get_me():
    try:
        user_id = get_jwt_identity()
        user = User.objects(id=user_id).first()
        if not user or not user.isActive:
            return jsonify({"status": "error", "message": "User not found or inactive"}), 401
        return jsonify({
            "status": "success",
            "user": user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500