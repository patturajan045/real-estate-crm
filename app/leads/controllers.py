# app/leads/controllers.py
from datetime import datetime
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from models import Lead, LeadNote, User
from mongoengine.errors import ValidationError, DoesNotExist
from mongoengine.queryset.visitor import Q
from app.notifications.controllers import create_followup_notification

def create_lead():
    try:
        data = request.get_json(force=True) or {}
        data.pop("leadId", None)
        data.pop("id", None)
        data.pop("_id", None)
        data.pop("initialNote", None)

        if not data.get("customerName") or not data.get("email") or not data.get("phoneNumber"):
            return jsonify({"status": "error", "message": "Customer name, email, and phone number are required."}), 400
        
        # Clean empty reference fields and dates
        if not data.get("assignedTo"):
            data.pop("assignedTo", None)
        else:
            data["assignedTo"] = User.objects(id=data["assignedTo"]).first()

        if data.get("budgetMin") not in (None, ""):
            try:
                data["budgetMin"] = float(data["budgetMin"])
            except (ValueError, TypeError):
                data.pop("budgetMin", None)
        else:
            data.pop("budgetMin", None)

        if data.get("budgetMax") not in (None, ""):
            try:
                data["budgetMax"] = float(data["budgetMax"])
            except (ValueError, TypeError):
                data.pop("budgetMax", None)
        else:
            data.pop("budgetMax", None)

        if data.get("nextFollowUpDate"):
            try:
                data["nextFollowUpDate"] = datetime.fromisoformat(data["nextFollowUpDate"].replace("Z", "+00:00"))
            except Exception:
                data.pop("nextFollowUpDate", None)
        else:
            data.pop("nextFollowUpDate", None)

        lead = Lead(**data).save()

        # In-App Notification if lead has an assigned user
        if lead.assignedTo:
            try:
                assigner_id = get_jwt_identity()
                create_followup_notification(
                    recipient=lead.assignedTo,
                    assigner=assigner_id,
                    customer_name=lead.customerName,
                    entity_type="lead",
                    entity_id=lead.id
                )
            except Exception:
                pass

        return jsonify({"status": "success", "data": lead.to_dict()}), 201
    except ValidationError as e:
        return jsonify({"status": "error", "message": "Invalid lead details submitted."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "Unable to create lead."}), 500

def get_leads():
    try:
        stage = request.args.get("stage")
        assigned_to = request.args.get("assignedTo")
        search = request.args.get("search")

        query = Q()
        if stage and stage != "All":
            query &= Q(stage=stage)
        if assigned_to:
            query &= Q(assignedTo=assigned_to)
        if search:
            query &= (Q(customerName__icontains=search) | Q(email__icontains=search) | Q(phoneNumber__icontains=search))

        leads = Lead.objects(query).order_by('-addedTime')
        return jsonify({"status": "success", "data": [l.to_dict() for l in leads]}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def get_lead(lead_id):
    try:
        lead = Lead.objects.get(id=lead_id)
        return jsonify({"status": "success", "data": lead.to_dict()}), 200
    except DoesNotExist:
        return jsonify({"status": "error", "message": "Lead not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def update_lead(lead_id):
    try:
        data = request.get_json(force=True) or {}
        lead = Lead.objects.get(id=lead_id)

        prev_assigned_id = str(lead.assignedTo.id) if lead.assignedTo else None
        prev_followup = lead.nextFollowUpDate

        # Handle simple string / numeric fields
        simple_fields = [
            "customerName", "email", "phoneNumber", "address", 
            "city", "stage", "source", "preferredUnitType"
        ]
        for field in simple_fields:
            if field in data:
                setattr(lead, field, data[field])

        if "budgetMin" in data and data["budgetMin"] != "":
            try:
                lead.budgetMin = float(data["budgetMin"])
            except Exception:
                pass

        if "budgetMax" in data and data["budgetMax"] != "":
            try:
                lead.budgetMax = float(data["budgetMax"])
            except Exception:
                pass

        # Handle assignedTo
        if "assignedTo" in data:
            if not data["assignedTo"]:
                lead.assignedTo = None
            else:
                user = User.objects(id=data["assignedTo"]).first()
                if user:
                    lead.assignedTo = user

        # Handle nextFollowUpDate
        if "nextFollowUpDate" in data:
            if not data["nextFollowUpDate"]:
                lead.nextFollowUpDate = None
            else:
                try:
                    lead.nextFollowUpDate = datetime.fromisoformat(data["nextFollowUpDate"].replace("Z", "+00:00"))
                except Exception:
                    pass

        lead.save()

        # In-App Notification if assigned or follow-up changed
        if lead.assignedTo:
            curr_assigned_id = str(lead.assignedTo.id)
            is_new_assignment = (curr_assigned_id != prev_assigned_id)
            is_new_followup = (lead.nextFollowUpDate and lead.nextFollowUpDate != prev_followup)
            if is_new_assignment or is_new_followup:
                try:
                    assigner_id = get_jwt_identity()
                    create_followup_notification(
                        recipient=lead.assignedTo,
                        assigner=assigner_id,
                        customer_name=lead.customerName,
                        entity_type="lead",
                        entity_id=lead.id
                    )
                except Exception:
                    pass

        return jsonify({"status": "success", "data": lead.to_dict()}), 200
    except DoesNotExist:
        return jsonify({"status": "error", "message": "Lead not found"}), 404
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def delete_lead(lead_id):
    try:
        lead = Lead.objects.get(id=lead_id)
        lead.delete()
        return jsonify({"status": "success", "message": "Lead deleted successfully"}), 200
    except DoesNotExist:
        return jsonify({"status": "error", "message": "Lead not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def add_lead_note(lead_id):
    try:
        data = request.get_json(force=True) or {}
        lead = Lead.objects.get(id=lead_id)
        prev_followup = lead.nextFollowUpDate
        
        note_data = {
            "authorId": data.get("authorId", "system"),
            "authorName": data.get("authorName", "Agent"),
            "content": data.get("content", "")
        }
        note = LeadNote(**note_data)
        lead.notes.append(note)

        # Update nextFollowUpDate if provided in the note form
        follow_up_updated = False
        if data.get("nextFollowUpDate"):
            try:
                new_date = datetime.fromisoformat(data["nextFollowUpDate"].replace("Z", "+00:00"))
                if lead.nextFollowUpDate != new_date:
                    lead.nextFollowUpDate = new_date
                    follow_up_updated = True
            except Exception:
                pass

        if data.get("stage") and data["stage"] in Lead.STAGES:
            lead.stage = data["stage"]

        lead.save()

        # In-App Notification if follow-up changed and lead is assigned
        if follow_up_updated and lead.assignedTo:
            try:
                assigner_id = get_jwt_identity()
                create_followup_notification(
                    recipient=lead.assignedTo,
                    assigner=assigner_id,
                    customer_name=lead.customerName,
                    entity_type="lead",
                    entity_id=lead.id,
                    note=note_data.get("content")
                )
            except Exception:
                pass

        return jsonify({"status": "success", "data": lead.to_dict()}), 201
    except DoesNotExist:
        return jsonify({"status": "error", "message": "Lead not found"}), 404
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500