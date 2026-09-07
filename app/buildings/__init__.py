from flask import Blueprint

buildingsBp = Blueprint('buildingsBp', __name__)

from . import routes