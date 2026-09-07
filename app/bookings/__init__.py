from flask import Blueprint

bookingsBp = Blueprint('bookingsBp', __name__)

from . import routes