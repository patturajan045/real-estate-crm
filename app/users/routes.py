from flask_jwt_extended import jwt_required
from . import usersBp
from .controllers import (
    create_user,
    get_all_users,
    get_user,
    update_user,
    delete_user
)

# ---------------------------
# USER CRUD ROUTES
# ---------------------------

@usersBp.route("/", methods=["POST"])
def route_create_user():
    return create_user()

@usersBp.route("/", methods=["GET"])
def route_get_all_users():
    return get_all_users()

@usersBp.route("/<user_id>", methods=["GET"])
def route_get_user(user_id):
    return get_user(user_id)

@usersBp.route("/<user_id>", methods=["PUT"])
def route_update_user(user_id):
    return update_user(user_id)

@usersBp.route("/<user_id>", methods=["DELETE"])
@jwt_required(optional=True)
def route_delete_user(user_id):
    return delete_user(user_id)