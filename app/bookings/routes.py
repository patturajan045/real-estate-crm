from flask_jwt_extended import jwt_required
from . import bookingsBp
from .controllers import create_booking, get_bookings, get_booking, cancel_booking

@bookingsBp.route("/", methods=["POST"])
@jwt_required(optional=True)
def route_create_booking(): return create_booking()

@bookingsBp.route("/", methods=["GET"])
def route_get_bookings(): return get_bookings()

@bookingsBp.route("/<booking_id>", methods=["GET"])
def route_get_booking(booking_id): return get_booking(booking_id)

@bookingsBp.route("/<booking_id>/cancel", methods=["POST"])
def route_cancel_booking(booking_id): return cancel_booking(booking_id)