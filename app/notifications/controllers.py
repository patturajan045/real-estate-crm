# app/notifications/controllers.py
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity
from models import Notification, User

def create_followup_notification(recipient, assigner=None, customer_name="Customer", entity_type="lead", entity_id=None, note=None):
    """
    Creates and saves an in-app notification when a lead or booking follow-up is assigned.
    """
    if not recipient:
        return None
    try:
        # Resolve recipient to User instance if given as ID
        if isinstance(recipient, (str, bytes)):
            recipient_user = User.objects(id=str(recipient)).first()
        elif hasattr(recipient, 'id'):
            recipient_user = recipient
        else:
            recipient_user = None

        if not recipient_user:
            return None

        # Resolve assigner
        sender_user = None
        assigner_name = "Administrator"
        if assigner:
            if isinstance(assigner, (str, bytes)):
                sender_user = User.objects(id=str(assigner)).first()
                if sender_user:
                    assigner_name = sender_user.name
            elif hasattr(assigner, 'name'):
                sender_user = assigner
                assigner_name = assigner.name

        title = "Follow-up Assigned" if entity_type == "lead" else "Booking Follow-up"
        msg = f"Follow-up assigned by {assigner_name} for {customer_name}."
        if note:
            clean_note = str(note).strip()
            if clean_note:
                msg += f" Note: {clean_note}"

        notif = Notification(
            recipient=recipient_user,
            sender=sender_user,
            senderName=assigner_name,
            title=title,
            message=msg,
            entityType=entity_type,
            entityId=str(entity_id) if entity_id else ""
        ).save()
        return notif
    except Exception as e:
        print(f"Warning: Failed to create follow-up notification: {e}")
        return None


def get_user_notifications():
    """Retrieve notifications for the currently authenticated user."""
    try:
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        notifications = Notification.objects(recipient=current_user_id).order_by('-createdTime')[:20]
        unread_count = Notification.objects(recipient=current_user_id, isRead=False).count()

        return jsonify({
            "status": "success",
            "unreadCount": unread_count,
            "data": [n.to_dict() for n in notifications]
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def mark_notification_read(notification_id):
    """Mark a specific notification as read."""
    try:
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        notif = Notification.objects(id=notification_id, recipient=current_user_id).first()
        if not notif:
            return jsonify({"status": "error", "message": "Notification not found"}), 404

        notif.isRead = True
        notif.save()

        return jsonify({"status": "success", "message": "Notification marked as read"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def mark_all_read():
    """Mark all notifications for the current user as read."""
    try:
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({"status": "error", "message": "Authentication required"}), 401

        Notification.objects(recipient=current_user_id, isRead=False).update(set__isRead=True)
        return jsonify({"status": "success", "message": "All notifications marked as read"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
