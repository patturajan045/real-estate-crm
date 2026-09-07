from flask_jwt_extended import jwt_required
from . import cmsBp
from .controllers import (
    get_all_content,
    get_grouped_content,
    update_content,
    batch_update_content,
    reset_default_content
)

@cmsBp.route("/content", methods=["GET"])
def route_get_all_content():
    return get_all_content()

@cmsBp.route("/content/grouped", methods=["GET"])
def route_get_grouped_content():
    return get_grouped_content()

@cmsBp.route("/content/<section_key>", methods=["PUT"])
@jwt_required()
def route_update_content(section_key):
    return update_content(section_key)

@cmsBp.route("/content/batch", methods=["PUT", "POST"])
@jwt_required()
def route_batch_update_content():
    return batch_update_content()

@cmsBp.route("/reset", methods=["POST"])
@jwt_required()
def route_reset_default_content():
    return reset_default_content()
