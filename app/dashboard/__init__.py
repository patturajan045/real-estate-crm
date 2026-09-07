# app/dashboard/__init__.py
from flask import Blueprint

dashboardBp = Blueprint('dashboardBp', __name__)

from . import routes
