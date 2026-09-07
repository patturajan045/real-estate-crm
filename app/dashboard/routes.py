# app/dashboard/routes.py
from . import dashboardBp
from .controllers import get_dashboard_stats

@dashboardBp.route("/stats", methods=["GET"])
def route_get_stats():
    return get_dashboard_stats()
