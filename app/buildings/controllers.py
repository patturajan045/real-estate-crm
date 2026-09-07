# app/buildings/controllers.py
from flask import request, jsonify
from models import Building, Project
from mongoengine.errors import ValidationError, DoesNotExist

def create_building():
    try:
        data = request.get_json(force=True) or {}
        data.pop("buildingId", None)
        data.pop("id", None)
        data.pop("_id", None)

        if not data.get("name"):
            return jsonify({"status": "error", "message": "Building name is required."}), 400

        if not data.get("project"):
            return jsonify({"status": "error", "message": "Project is required."}), 400
        
        project = Project.objects(id=data["project"]).first()
        if not project:
            return jsonify({"status": "error", "message": "Referenced Project not found."}), 404
        data["project"] = project

        if "totalFloors" in data:
            try:
                data["totalFloors"] = int(data["totalFloors"])
            except (ValueError, TypeError):
                data["totalFloors"] = 1

        building = Building(**data).save()
        return jsonify({"status": "success", "data": building.to_dict()}), 201
    except ValidationError as e:
        return jsonify({"status": "error", "message": "Invalid building data submitted."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "Unable to create building."}), 500

def get_all_buildings():
    try:
        project_id = request.args.get("project_id")
        if project_id:
            buildings = Building.objects(project=project_id).order_by('name')
        else:
            buildings = Building.objects().order_by('-addedTime')
        return jsonify({"status": "success", "data": [b.to_dict() for b in buildings]}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Unable to fetch buildings."}), 500

def get_buildings(project_id):
    try:
        buildings = Building.objects(project=project_id).order_by('name')
        return jsonify({"status": "success", "data": [b.to_dict() for b in buildings]}), 200
    except ValidationError:
        return jsonify({"status": "error", "message": "Invalid project ID format."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "Unable to fetch project buildings."}), 500

def get_building(building_id):
    try:
        building = Building.objects.get(id=building_id)
        return jsonify({"status": "success", "data": building.to_dict()}), 200
    except DoesNotExist:
        return jsonify({"status": "error", "message": "Building not found."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": "Unable to retrieve building."}), 500

def update_building(building_id):
    try:
        data = request.get_json(force=True) or {}
        data.pop("buildingId", None)
        data.pop("id", None)
        data.pop("_id", None)

        building = Building.objects.get(id=building_id)
        if "project" in data and data["project"]:
            proj = Project.objects(id=data["project"]).first()
            if proj:
                building.project = proj
            data.pop("project", None)

        if "totalFloors" in data:
            try:
                building.totalFloors = int(data["totalFloors"])
            except (ValueError, TypeError):
                pass
            data.pop("totalFloors", None)

        for key, val in data.items():
            if hasattr(building, key):
                setattr(building, key, val)
        building.save()
        return jsonify({"status": "success", "data": building.to_dict()}), 200
    except DoesNotExist:
        return jsonify({"status": "error", "message": "Building not found."}), 404
    except ValidationError as e:
        return jsonify({"status": "error", "message": "Invalid building details provided."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "Unable to update building."}), 500

def delete_building(building_id):
    try:
        building = Building.objects.get(id=building_id)
        building.delete()
        return jsonify({"status": "success", "message": "Building deleted successfully."}), 200
    except DoesNotExist:
        return jsonify({"status": "error", "message": "Building not found."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": "Unable to delete building."}), 500