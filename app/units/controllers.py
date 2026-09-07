# app/units/controllers.py
from flask import request, jsonify
from models import Unit, Project, Building
from mongoengine.errors import ValidationError, DoesNotExist, NotUniqueError
from mongoengine.queryset.visitor import Q

def create_unit():
    try:
        data = request.get_json(force=True) or {}
        data.pop("unitId", None)
        data.pop("id", None)
        data.pop("_id", None)
        
        if not data.get("unitNumber"):
            return jsonify({"status": "error", "message": "Unit number is required."}), 400

        if "project" in data and isinstance(data["project"], str):
            project = Project.objects(id=data["project"]).first()
            if not project:
                return jsonify({"status": "error", "message": "Referenced Project not found."}), 404
            data["project"] = project

        if "building" in data and isinstance(data["building"], str):
            building = Building.objects(id=data["building"]).first()
            if not building:
                return jsonify({"status": "error", "message": "Referenced Building not found."}), 404
            data["building"] = building

        if "floor" in data:
            try:
                data["floor"] = int(data["floor"])
            except (ValueError, TypeError):
                data["floor"] = 1

        if "carpetAreaSqFt" in data:
            try:
                data["carpetAreaSqFt"] = float(data["carpetAreaSqFt"])
            except (ValueError, TypeError):
                data["carpetAreaSqFt"] = 0.0

        if "price" in data:
            try:
                data["price"] = float(data["price"])
            except (ValueError, TypeError):
                data["price"] = 0.0

        unit = Unit(**data).save()
        return jsonify({"status": "success", "data": unit.to_dict()}), 201
    except NotUniqueError:
        return jsonify({"status": "error", "message": "A unit with this number already exists in this building."}), 409
    except ValidationError:
        return jsonify({"status": "error", "message": "Invalid unit data submitted."}), 400
    except Exception:
        return jsonify({"status": "error", "message": "Unable to create unit."}), 500

def get_all_units():
    try:
        project_id = request.args.get("project_id")
        building_id = request.args.get("building_id")
        status = request.args.get("status")
        unit_type = request.args.get("unit_type")

        query = Q()
        if project_id:
            query &= Q(project=project_id)
        if building_id:
            query &= Q(building=building_id)
        if status and status != "All":
            query &= Q(status=status)
        if unit_type and unit_type != "All":
            query &= Q(unitType=unit_type)

        units = Unit.objects(query).order_by('floor', 'unitNumber')
        return jsonify({"status": "success", "data": [u.to_dict() for u in units]}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Unable to fetch units."}), 500

def get_units(building_id):
    try:
        units = Unit.objects(building=building_id).order_by('floor', 'unitNumber')
        return jsonify({"status": "success", "data": [u.to_dict() for u in units]}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Unable to fetch building units."}), 500

def get_unit(unit_id):
    try:
        unit = Unit.objects.get(id=unit_id)
        return jsonify({"status": "success", "data": unit.to_dict()}), 200
    except DoesNotExist:
        return jsonify({"status": "error", "message": "Unit not found."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": "Unable to retrieve unit."}), 500

def update_unit(unit_id):
    try:
        data = request.get_json(force=True) or {}
        data.pop("unitId", None)
        data.pop("id", None)
        data.pop("_id", None)

        unit = Unit.objects.get(id=unit_id)

        if "project" in data and isinstance(data["project"], str):
            proj = Project.objects(id=data["project"]).first()
            if proj:
                unit.project = proj
            data.pop("project", None)

        if "building" in data and isinstance(data["building"], str):
            bld = Building.objects(id=data["building"]).first()
            if bld:
                unit.building = bld
            data.pop("building", None)

        if "floor" in data:
            try:
                unit.floor = int(data["floor"])
            except (ValueError, TypeError):
                pass
            data.pop("floor", None)

        if "carpetAreaSqFt" in data:
            try:
                unit.carpetAreaSqFt = float(data["carpetAreaSqFt"])
            except (ValueError, TypeError):
                pass
            data.pop("carpetAreaSqFt", None)

        if "price" in data:
            try:
                unit.price = float(data["price"])
            except (ValueError, TypeError):
                pass
            data.pop("price", None)

        for key, val in data.items():
            if hasattr(unit, key):
                setattr(unit, key, val)

        unit.save()
        return jsonify({"status": "success", "data": unit.to_dict()}), 200
    except DoesNotExist:
        return jsonify({"status": "error", "message": "Unit not found."}), 404
    except ValidationError as e:
        return jsonify({"status": "error", "message": "Invalid unit details provided."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "Unable to update unit."}), 500

def update_unit_status(unit_id):
    try:
        data = request.get_json(force=True) or {}
        unit = Unit.objects.get(id=unit_id)
        if data.get("status"):
            unit.status = data.get("status")
            unit.save()
        return jsonify({"status": "success", "data": unit.to_dict()}), 200
    except DoesNotExist:
        return jsonify({"status": "error", "message": "Unit not found."}), 404
    except ValidationError as e:
        return jsonify({"status": "error", "message": "Invalid status value provided."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "Unable to update unit status."}), 500

def delete_unit(unit_id):
    try:
        unit = Unit.objects.get(id=unit_id)
        unit.delete()
        return jsonify({"status": "success", "message": "Unit deleted successfully."}), 200
    except DoesNotExist:
        return jsonify({"status": "error", "message": "Unit not found."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": "Unable to delete unit."}), 500