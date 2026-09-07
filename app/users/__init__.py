from flask import Blueprint

# Initialize the Blueprint for the users package
usersBp = Blueprint('usersBp', __name__)

# Import routes to register them with the blueprint
from . import routes