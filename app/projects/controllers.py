# app/projects/controllers.py
from flask import request, jsonify
from models import Project
from mongoengine.errors import ValidationError, DoesNotExist, NotUniqueError

def create_project():
    try:
        data = request.get_json(force=True) or {}
        # Remove hidden form fields if passed
        data.pop("projectId", None)
        data.pop("id", None)
        data.pop("_id", None)

        if not data.get("name") or not data.get("city"):
            return jsonify({"status": "error", "message": "Project name and city are required."}), 400

        project = Project(**data).save()
        return jsonify({"status": "success", "data": project.to_dict()}), 201
    except NotUniqueError:
        return jsonify({"status": "error", "message": "A project with this name already exists."}), 409
    except ValidationError:
        return jsonify({"status": "error", "message": "Invalid project data submitted."}), 400
    except Exception:
        return jsonify({"status": "error", "message": "Unable to create project."}), 500

def get_projects():
    try:
        projects = Project.objects().order_by('-addedTime')
        return jsonify({"status": "success", "data": [p.to_dict() for p in projects]}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Unable to fetch projects."}), 500

def get_project(project_id):
    try:
        project = Project.objects.get(id=project_id)
        return jsonify({"status": "success", "data": project.to_dict()}), 200
    except DoesNotExist:
        return jsonify({"status": "error", "message": "Project not found."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": "Unable to retrieve project."}), 500

def update_project(project_id):
    try:
        data = request.get_json(force=True) or {}
        data.pop("projectId", None)
        data.pop("id", None)
        data.pop("_id", None)

        project = Project.objects.get(id=project_id)
        for key, val in data.items():
            if hasattr(project, key):
                setattr(project, key, val)
        project.save()
        return jsonify({"status": "success", "data": project.to_dict()}), 200
    except DoesNotExist:
        return jsonify({"status": "error", "message": "Project not found."}), 404
    except ValidationError as e:
        return jsonify({"status": "error", "message": "Invalid project details provided."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "Unable to update project."}), 500

def delete_project(project_id):
    try:
        project = Project.objects.get(id=project_id)
        project.delete()
        return jsonify({"status": "success", "message": "Project deleted successfully."}), 200
    except DoesNotExist:
        return jsonify({"status": "error", "message": "Project not found."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": "Unable to delete project."}), 500