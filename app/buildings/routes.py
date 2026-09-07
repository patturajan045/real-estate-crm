from . import buildingsBp
from .controllers import (
    create_building, get_all_buildings, get_buildings, 
    get_building, update_building, delete_building
)

@buildingsBp.route("/", methods=["POST"])
def route_create_building(): return create_building()

@buildingsBp.route("/", methods=["GET"])
def route_get_all_buildings(): return get_all_buildings()

@buildingsBp.route("/project/<project_id>", methods=["GET"])
def route_get_buildings(project_id): return get_buildings(project_id)

@buildingsBp.route("/<building_id>", methods=["GET"])
def route_get_building(building_id): return get_building(building_id)

@buildingsBp.route("/<building_id>", methods=["PUT"])
def route_update_building(building_id): return update_building(building_id)

@buildingsBp.route("/<building_id>", methods=["DELETE"])
def route_delete_building(building_id): return delete_building(building_id)