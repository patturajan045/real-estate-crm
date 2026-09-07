# app/notifications/__init__.py
from flask import Blueprint

notificationsBp = Blueprint('notificationsBp', __name__)

from . import routes
