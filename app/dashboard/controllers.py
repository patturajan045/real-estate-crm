# app/dashboard/controllers.py
from datetime import datetime, time
from flask import jsonify, request
from models import Lead, Booking, Unit, Project, User

def get_dashboard_stats():
    try:
        now = datetime.utcnow()
        today_start = datetime.combine(now.date(), time.min)
        today_end = datetime.combine(now.date(), time.max)

        # 1. Leads Stats
        total_leads = Lead.objects.count()
        leads_by_stage = {stage: 0 for stage in Lead.STAGES}
        for lead in Lead.objects.only('stage'):
            if lead.stage in leads_by_stage:
                leads_by_stage[lead.stage] += 1

        # 2. Follow-ups Stats
        # Active leads with scheduled follow-ups
        active_leads = Lead.objects(stage__nin=[Lead.STAGE_BOOKED, Lead.STAGE_LOST], nextFollowUpDate__exists=True, nextFollowUpDate__ne=None)
        overdue_followups = []
        today_followups = []
        upcoming_followups = []

        for l in active_leads:
            if not l.nextFollowUpDate:
                continue
            item = {
                "id": str(l.id),
                "customerName": l.customerName,
                "phoneNumber": l.phoneNumber,
                "email": l.email,
                "stage": l.stage,
                "nextFollowUpDate": l.nextFollowUpDate.isoformat(),
                "assignedToName": getattr(l.assignedTo, "name", "Unassigned") if l.assignedTo else "Unassigned"
            }
            if l.nextFollowUpDate < today_start:
                overdue_followups.append(item)
            elif today_start <= l.nextFollowUpDate <= today_end:
                today_followups.append(item)
            else:
                upcoming_followups.append(item)

        # Sort followups chronologically
        overdue_followups.sort(key=lambda x: x["nextFollowUpDate"])
        today_followups.sort(key=lambda x: x["nextFollowUpDate"])
        upcoming_followups.sort(key=lambda x: x["nextFollowUpDate"])

        # 3. Property & Units Stats
        total_projects = Project.objects.count()
        total_units = Unit.objects.count()
        units_by_status = {status: 0 for status in Unit.STATUS_CHOICES}
        for u in Unit.objects.only('status'):
            if u.status in units_by_status:
                units_by_status[u.status] += 1

        # 4. Bookings & Financials Stats
        confirmed_bookings = Booking.objects(status=Booking.STATUS_CONFIRMED)
        total_bookings = confirmed_bookings.count()
        total_revenue = sum(b.agreementValue for b in confirmed_bookings)
        total_advance_collected = sum(b.bookingAmount for b in confirmed_bookings)

        # 5. Recent Activity
        recent_leads = [l.to_dict() for l in Lead.objects.order_by('-addedTime')[:5]]
        recent_bookings = [b.to_dict() for b in Booking.objects.order_by('-bookingDate')[:5]]

        return jsonify({
            "status": "success",
            "data": {
                "counts": {
                    "totalLeads": total_leads,
                    "totalProjects": total_projects,
                    "totalUnits": total_units,
                    "availableUnits": units_by_status.get(Unit.STATUS_AVAILABLE, 0),
                    "totalBookings": total_bookings,
                    "totalRevenue": total_revenue,
                    "totalAdvanceCollected": total_advance_collected,
                    "todayFollowupsCount": len(today_followups),
                    "overdueFollowupsCount": len(overdue_followups)
                },
                "leadsByStage": leads_by_stage,
                "unitsByStatus": units_by_status,
                "followups": {
                    "today": today_followups,
                    "overdue": overdue_followups,
                    "upcoming": upcoming_followups[:10]
                },
                "recentLeads": recent_leads,
                "recentBookings": recent_bookings
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
