# app/cms/__init__.py
from flask import Blueprint

cmsBp = Blueprint('cmsBp', __name__)

from . import routes
