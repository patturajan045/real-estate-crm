from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from models import Booking, Lead, Unit, User
from mongoengine.errors import ValidationError, DoesNotExist, NotUniqueError
from app.notifications.controllers import create_followup_notification

def create_booking():
    try:
        data = request.get_json(force=True) or {}
        
        unit_id = data.get("unit")
        lead_id = data.get("lead")
        booked_by_id = data.get("bookedBy")

        if not unit_id or not lead_id:
            return jsonify({"status": "error", "message": "Lead and Unit are required"}), 400

        lead = Lead.objects(id=lead_id).first()
        if not lead:
            return jsonify({"status": "error", "message": "Referenced Lead not found"}), 404

        unit = Unit.objects(id=unit_id).first()
        if not unit:
            return jsonify({"status": "error", "message": "Referenced Unit not found"}), 404

        booked_by_user = None
        if booked_by_id:
            booked_by_user = User.objects(id=booked_by_id).first()
        if not booked_by_user:
            # Fallback to lead's assigned user or first admin/user
            booked_by_user = lead.assignedTo or User.objects.first()

        # ATOMIC CONCURRENCY GUARD:
        # Atomic check and update ensures two concurrent users cannot book the same unit.
        # If updated_count == 0, another request already claimed this unit!
        updated_count = Unit.objects(id=unit_id, status=Unit.STATUS_AVAILABLE).update_one(set__status=Unit.STATUS_BOOKED)
        if updated_count == 0:
            return jsonify({
                "status": "error", 
                "message": f"Double booking prevented! Unit '{unit.unitNumber}' is not available (already booked or sold)."
            }), 409

        try:
            booking = Booking(
                lead=lead,
                unit=unit,
                bookedBy=booked_by_user,
                agreementValue=float(data.get("agreementValue", unit.price)),
                bookingAmount=float(data.get("bookingAmount", 0.0)),
                paymentMethod=data.get("paymentMethod", "Bank Transfer"),
                transactionReference=data.get("transactionReference", ""),
                status=Booking.STATUS_CONFIRMED
            ).save()

            # Update lead stage to Booked
            lead.stage = Lead.STAGE_BOOKED
            lead.save()

            # In-App Notification for booking follow-up/assignment
            try:
                assigner_id = get_jwt_identity()
                notify_target = booked_by_user or lead.assignedTo
                if notify_target:
                    create_followup_notification(
                        recipient=notify_target,
                        assigner=assigner_id,
                        customer_name=lead.customerName,
                        entity_type="booking",
                        entity_id=booking.id,
                        note=f"Unit {unit.unitNumber} booked."
                    )
            except Exception:
                pass

            return jsonify({"status": "success", "data": booking.to_dict()}), 201

        except Exception as e:
            # Rollback unit status back to Available if booking creation failed
            Unit.objects(id=unit_id).update_one(set__status=Unit.STATUS_AVAILABLE)
            raise e
    
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message}), 400
    except NotUniqueError:
        return jsonify({"status": "error", "message": "A confirmed booking already exists for this unit."}), 409
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def get_bookings():
    try:
        status = request.args.get("status")
        if status and status != "All":
            bookings = Booking.objects(status=status).order_by('-bookingDate')
        else:
            bookings = Booking.objects().order_by('-bookingDate')
        return jsonify({"status": "success", "data": [b.to_dict() for b in bookings]}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def get_booking(booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
        return jsonify({"status": "success", "data": booking.to_dict()}), 200
    except DoesNotExist:
        return jsonify({"status": "error", "message": "Booking not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def cancel_booking(booking_id):
    try:
        data = request.get_json(silent=True) or {}
        booking = Booking.objects.get(id=booking_id)

        if booking.status == Booking.STATUS_CANCELLED:
            return jsonify({"status": "error", "message": "Booking is already cancelled"}), 400

        booking.status = Booking.STATUS_CANCELLED
        booking.cancellationReason = data.get("cancellationReason", "Cancelled by user")
        booking.save()

        # Release unit back to Available
        if booking.unit:
            Unit.objects(id=booking.unit.id).update_one(set__status=Unit.STATUS_AVAILABLE)

        return jsonify({"status": "success", "data": booking.to_dict()}), 200
    except DoesNotExist:
        return jsonify({"status": "error", "message": "Booking not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500