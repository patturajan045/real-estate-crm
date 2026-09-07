from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from werkzeug.security import generate_password_hash
from models import User, Lead

def create_user():
    """Create a new user (Admin or Sales Employee)."""
    data = request.get_json(force=True) or {}
    
    # Required fields
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", User.ROLE_SALES)

    if not name or not email or not password:
        return jsonify({
            "status": "error", 
            "message": "Missing required fields: name, email, password"
        }), 400

    # Check for existing user
    if User.objects(email=email).first():
        return jsonify({
            "status": "error", 
            "message": "User with this email already exists"
        }), 409

    try:
        new_user = User(
            name=name,
            email=email,
            phoneNumber=data.get("phoneNumber"),
            password=generate_password_hash(password),
            role=role,
            isActive=data.get("isActive", True)
        )
        new_user.save()

        return jsonify({
            "status": "success",
            "message": "User created successfully",
            "data": new_user.to_dict()
        }), 201

    except Exception as e:
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500


def get_all_users():
    """Retrieve all users."""
    try:
        users = User.objects().order_by('-addedTime')
        return jsonify({
            "status": "success",
            "data": [user.to_dict() for user in users]
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500


def get_user(user_id):
    """Retrieve a single user by ID."""
    try:
        user = User.objects(id=user_id).first()
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        return jsonify({"status": "success", "data": user.to_dict()}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500


def update_user(user_id):
    """Update user details."""
    data = request.get_json(force=True) or {}
    
    try:
        user = User.objects(id=user_id).first()
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        # Update allowed fields
        if "name" in data:
            user.name = data["name"]
        if "phoneNumber" in data:
            user.phoneNumber = data["phoneNumber"]
        if "role" in data and data["role"] in User.ROLES:
            user.role = data["role"]
        if "isActive" in data:
            user.isActive = data["isActive"]
        
        # Handle password update securely
        if "password" in data and data["password"]:
            user.password = generate_password_hash(data["password"])

        user.save()

        return jsonify({
            "status": "success",
            "message": "User updated successfully",
            "data": user.to_dict()
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500


def delete_user(user_id):
    """
    Deactivates active users, or permanently deletes inactive users.
    When a user is inactive (unactive), allows permanent deletion.
    """
    try:
        current_user_id = get_jwt_identity()
        if current_user_id and str(current_user_id) == str(user_id):
            return jsonify({"status": "error", "message": "You cannot delete your own account."}), 400

        user = User.objects(id=user_id).first()
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        permanent = request.args.get("permanent", "false").lower() == "true" or not user.isActive

        if permanent:
            # Permanent deletion: clean up any lead assignments first
            Lead.objects(assignedTo=user.id).update(set__assignedTo=None)
            user_name = user.name
            user.delete()
            return jsonify({
                "status": "success",
                "message": f"User '{user_name}' permanently deleted successfully"
            }), 200
        else:
            # Deactivate active user
            user.isActive = False
            user.save()
            return jsonify({
                "status": "success",
                "message": f"User '{user.name}' deactivated successfully. Inactive users can now be permanently deleted.",
                "data": user.to_dict()
            }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500