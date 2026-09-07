from flask_jwt_extended import jwt_required
from . import leadsBp
from .controllers import (
    create_lead, get_leads, get_lead, 
    update_lead, delete_lead, add_lead_note
)

@leadsBp.route("/", methods=["POST"])
@jwt_required(optional=True)
def route_create_lead(): return create_lead()

@leadsBp.route("/", methods=["GET"])
def route_get_leads(): return get_leads()

@leadsBp.route("/<lead_id>", methods=["GET"])
def route_get_lead(lead_id): return get_lead(lead_id)

@leadsBp.route("/<lead_id>", methods=["PUT"])
@jwt_required(optional=True)
def route_update_lead(lead_id): return update_lead(lead_id)

@leadsBp.route("/<lead_id>", methods=["DELETE"])
def route_delete_lead(lead_id): return delete_lead(lead_id)

@leadsBp.route("/<lead_id>/notes", methods=["POST"])
@jwt_required(optional=True)
def route_add_note(lead_id): return add_lead_note(lead_id)