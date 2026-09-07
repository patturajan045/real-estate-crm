from . import unitsBp
from .controllers import (
    create_unit, get_all_units, get_units, 
    get_unit, update_unit, update_unit_status, delete_unit
)

@unitsBp.route("/", methods=["POST"])
def route_create_unit(): return create_unit()

@unitsBp.route("/", methods=["GET"])
def route_get_all_units(): return get_all_units()

@unitsBp.route("/building/<building_id>", methods=["GET"])
def route_get_units(building_id): return get_units(building_id)

@unitsBp.route("/<unit_id>", methods=["GET"])
def route_get_unit(unit_id): return get_unit(unit_id)

@unitsBp.route("/<unit_id>", methods=["PUT"])
def route_update_unit(unit_id): return update_unit(unit_id)

@unitsBp.route("/<unit_id>/status", methods=["PATCH"])
def route_update_status(unit_id): return update_unit_status(unit_id)

@unitsBp.route("/<unit_id>", methods=["DELETE"])
def route_delete_unit(unit_id): return delete_unit(unit_id)