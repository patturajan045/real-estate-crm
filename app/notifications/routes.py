# app/notifications/routes.py
from flask_jwt_extended import jwt_required
from . import notificationsBp
from .controllers import (
    get_user_notifications,
    mark_notification_read,
    mark_all_read
)

@notificationsBp.route("/", methods=["GET"])
@jwt_required()
def route_get_notifications():
    return get_user_notifications()

@notificationsBp.route("/<notification_id>/read", methods=["POST"])
@jwt_required()
def route_mark_notification_read(notification_id):
    return mark_notification_read(notification_id)

@notificationsBp.route("/mark-all-read", methods=["POST"])
@jwt_required()
def route_mark_all_read():
    return mark_all_read()
