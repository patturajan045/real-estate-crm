from . import projectsBp
from .controllers import create_project, get_projects, get_project, update_project, delete_project

@projectsBp.route("/", methods=["POST"])
def route_create_project(): return create_project()

@projectsBp.route("/", methods=["GET"])
def route_get_projects(): return get_projects()

@projectsBp.route("/<project_id>", methods=["GET"])
def route_get_project(project_id): return get_project(project_id)

@projectsBp.route("/<project_id>", methods=["PUT"])
def route_update_project(project_id): return update_project(project_id)

@projectsBp.route("/<project_id>", methods=["DELETE"])
def route_delete_project(project_id): return delete_project(project_id)