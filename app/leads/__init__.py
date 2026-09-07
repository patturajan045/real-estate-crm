from flask import Blueprint

leadsBp = Blueprint('leadsBp', __name__)

from . import routes