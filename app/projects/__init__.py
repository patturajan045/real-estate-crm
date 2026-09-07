from flask import Blueprint

projectsBp = Blueprint('projectsBp', __name__)

from . import routes