from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from models import PageContent, User
from mongoengine.errors import ValidationError, DoesNotExist

DEFAULT_PAGE_CONTENTS = [
    # Login Page
    {"page": "login", "sectionKey": "login_brand_title", "label": "Login Brand Title", "content": "EstateFlow CRM", "contentType": "title", "sortOrder": 1},
    {"page": "login", "sectionKey": "login_brand_subtitle", "label": "Login Brand Subtitle", "content": "Real Estate Sales & Booking Platform", "contentType": "subtitle", "sortOrder": 2},
    {"page": "login", "sectionKey": "login_heading", "label": "Login Card Heading", "content": "Sign In to Your Account", "contentType": "heading", "sortOrder": 3},
    {"page": "login", "sectionKey": "login_subheading", "label": "Login Instruction Subheading", "content": "Enter your verified credentials to access your real estate workspace", "contentType": "paragraph", "sortOrder": 4},
    {"page": "login", "sectionKey": "login_label_identifier", "label": "Login Field Label", "content": "Email or Username", "contentType": "heading", "sortOrder": 5},
    {"page": "login", "sectionKey": "login_footer_text", "label": "Login Footer Copyright / Note", "content": "© 2026 EstateFlow CRM. Protected by JWT Authentication.", "contentType": "paragraph", "sortOrder": 6},

    # Register Page
    {"page": "register", "sectionKey": "register_brand_title", "label": "Register Brand Title", "content": "EstateFlow CRM", "contentType": "title", "sortOrder": 1},
    {"page": "register", "sectionKey": "register_brand_subtitle", "label": "Register Brand Subtitle", "content": "Real Estate Sales & Booking Platform", "contentType": "subtitle", "sortOrder": 2},
    {"page": "register", "sectionKey": "register_heading", "label": "Register Card Heading", "content": "Create Team Account", "contentType": "heading", "sortOrder": 3},
    {"page": "register", "sectionKey": "register_subheading", "label": "Register Instruction Subheading", "content": "Join the sales and property management team", "contentType": "paragraph", "sortOrder": 4},
    {"page": "register", "sectionKey": "register_footer_text", "label": "Register Footer Note", "content": "Role permissions will be verified according to administrative policy.", "contentType": "paragraph", "sortOrder": 5},

    # Dashboard Page
    {"page": "dashboard", "sectionKey": "dashboard_title", "label": "Dashboard Page Title", "content": "Sales & Inventory Dashboard", "contentType": "title", "sortOrder": 1},
    {"page": "dashboard", "sectionKey": "dashboard_subtitle", "label": "Dashboard Page Subtitle", "content": "Live metrics, lead pipeline progress, and upcoming follow-ups", "contentType": "subtitle", "sortOrder": 2},
    {"page": "dashboard", "sectionKey": "dashboard_welcome_text", "label": "Dashboard Welcome Note", "content": "Welcome back! Here is an overview of your property leads and inventory performance.", "contentType": "paragraph", "sortOrder": 3},
    {"page": "dashboard", "sectionKey": "dashboard_pipeline_heading", "label": "Pipeline Chart Heading", "content": "Leads by Pipeline Stage", "contentType": "heading", "sortOrder": 4},
    {"page": "dashboard", "sectionKey": "dashboard_inventory_heading", "label": "Inventory Chart Heading", "content": "Unit Inventory Status", "contentType": "heading", "sortOrder": 5},
    {"page": "dashboard", "sectionKey": "dashboard_followups_heading", "label": "Follow-ups Section Heading", "content": "Pending & Urgent Follow-ups", "contentType": "heading", "sortOrder": 6},
    {"page": "dashboard", "sectionKey": "dashboard_bookings_heading", "label": "Recent Bookings Heading", "content": "Recent Bookings & Agreements", "contentType": "heading", "sortOrder": 7},

    # Leads Page
    {"page": "leads", "sectionKey": "leads_title", "label": "Leads Page Title", "content": "Leads Management", "contentType": "title", "sortOrder": 1},
    {"page": "leads", "sectionKey": "leads_subtitle", "label": "Leads Page Subtitle", "content": "Manage prospect pipeline, schedule follow-ups, and convert leads to bookings", "contentType": "subtitle", "sortOrder": 2},
    {"page": "leads", "sectionKey": "leads_notice_text", "label": "Leads Notice Note", "content": "Click any lead to view call history, log notes, or convert directly to a property booking.", "contentType": "paragraph", "sortOrder": 3},

    # Properties Page
    {"page": "properties", "sectionKey": "properties_title", "label": "Properties Page Title", "content": "Property & Inventory Management", "contentType": "title", "sortOrder": 1},
    {"page": "properties", "sectionKey": "properties_subtitle", "label": "Properties Page Subtitle", "content": "Explore real estate projects, buildings, and unit availability in real time", "contentType": "subtitle", "sortOrder": 2},
    {"page": "properties", "sectionKey": "properties_units_heading", "label": "Units Tab Heading", "content": "Real-time Property Units Inventory", "contentType": "heading", "sortOrder": 3},
    {"page": "properties", "sectionKey": "properties_projects_heading", "label": "Projects Tab Heading", "content": "Master Real Estate Projects", "contentType": "heading", "sortOrder": 4},
    {"page": "properties", "sectionKey": "properties_buildings_heading", "label": "Buildings Tab Heading", "content": "Towers & Buildings Directory", "contentType": "heading", "sortOrder": 5},

    # Bookings Page
    {"page": "bookings", "sectionKey": "bookings_title", "label": "Bookings Page Title", "content": "Bookings Management", "contentType": "title", "sortOrder": 1},
    {"page": "bookings", "sectionKey": "bookings_subtitle", "label": "Bookings Page Subtitle", "content": "Connect customer leads with property units and process reservation agreements", "contentType": "subtitle", "sortOrder": 2},
    {"page": "bookings", "sectionKey": "bookings_protection_notice", "label": "Double Booking Guard Notice", "content": "Double Booking Protection: Unit availability is atomically secured. If another agent reserves the same unit concurrently, your agreement will be safely protected from collision.", "contentType": "notice", "sortOrder": 3},

    # Users Page
    {"page": "users", "sectionKey": "users_title", "label": "Users Page Title", "content": "Team & User Management", "contentType": "title", "sortOrder": 1},
    {"page": "users", "sectionKey": "users_subtitle", "label": "Users Page Subtitle", "content": "Manage employee accounts, permissions, and roles (Super Admin, Admin, Sales Employee)", "contentType": "subtitle", "sortOrder": 2},
    {"page": "users", "sectionKey": "users_role_policy_notice", "label": "User Policy Notice", "content": "Role-Based Access Control: Super Admin has full authority, Admin manages team & inventory, Sales Employees manage leads & bookings.", "contentType": "notice", "sortOrder": 3},

    # Settings (CMS) Page
    {"page": "settings", "sectionKey": "settings_title", "label": "Settings Page Title", "content": "Platform Content & Dynamic Headings", "contentType": "title", "sortOrder": 1},
    {"page": "settings", "sectionKey": "settings_subtitle", "label": "Settings Page Subtitle", "content": "Customize all headings, titles, subheadings, and paragraphs dynamically across the system", "contentType": "subtitle", "sortOrder": 2},
    {"page": "settings", "sectionKey": "settings_info_banner", "label": "Settings Instructions Banner", "content": "All changes saved here update system records instantly and apply across the entire portal for all users without code changes.", "contentType": "paragraph", "sortOrder": 3},

    # Global Navigation & Sidebar (base.html)
    {"page": "navigation", "sectionKey": "nav_brand_name", "label": "Sidebar Brand Name", "content": "EstateFlow", "contentType": "title", "sortOrder": 1},
    {"page": "navigation", "sectionKey": "nav_brand_subtitle", "label": "Sidebar Brand Subtitle", "content": "Real Estate CRM", "contentType": "subtitle", "sortOrder": 2},
    {"page": "navigation", "sectionKey": "nav_menu_overview", "label": "Menu Header: Overview", "content": "Overview", "contentType": "heading", "sortOrder": 3},
    {"page": "navigation", "sectionKey": "nav_menu_dashboard", "label": "Menu Item: Dashboard", "content": "Dashboard", "contentType": "title", "sortOrder": 4},
    {"page": "navigation", "sectionKey": "nav_menu_pipeline", "label": "Menu Header: Sales Pipeline", "content": "Sales Pipeline", "contentType": "heading", "sortOrder": 5},
    {"page": "navigation", "sectionKey": "nav_menu_leads", "label": "Menu Item: Leads", "content": "Leads", "contentType": "title", "sortOrder": 6},
    {"page": "navigation", "sectionKey": "nav_menu_bookings", "label": "Menu Item: Bookings", "content": "Bookings", "contentType": "title", "sortOrder": 7},
    {"page": "navigation", "sectionKey": "nav_menu_inventory", "label": "Menu Header: Inventory", "content": "Inventory", "contentType": "heading", "sortOrder": 8},
    {"page": "navigation", "sectionKey": "nav_menu_properties", "label": "Menu Item: Properties & Units", "content": "Properties & Units", "contentType": "title", "sortOrder": 9},
    {"page": "navigation", "sectionKey": "nav_menu_admin", "label": "Menu Header: Administration", "content": "Administration", "contentType": "heading", "sortOrder": 10},
    {"page": "navigation", "sectionKey": "nav_menu_users", "label": "Menu Item: Users & Team", "content": "Users & Team", "contentType": "title", "sortOrder": 11},
    {"page": "navigation", "sectionKey": "nav_menu_settings", "label": "Menu Item: Platform Settings", "content": "Platform Settings", "contentType": "title", "sortOrder": 12},
    {"page": "navigation", "sectionKey": "nav_btn_logout", "label": "Header Logout Button Label", "content": "Logout", "contentType": "title", "sortOrder": 13},
]

def seed_cms_defaults_if_needed():
    """Ensures all default dynamic headings exist in the database."""
    for item in DEFAULT_PAGE_CONTENTS:
        if not PageContent.objects(sectionKey=item["sectionKey"]).first():
            PageContent(**item).save()

def get_all_content():
    """Returns key-value map and raw list for dynamic DOM substitution."""
    try:
        seed_cms_defaults_if_needed()
        contents = PageContent.objects().order_by('page', 'sortOrder')
        kv_map = {c.sectionKey: c.content for c in contents}
        return jsonify({
            "status": "success",
            "data": kv_map,
            "items": [c.to_dict() for c in contents]
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def get_grouped_content():
    """Returns content grouped by page for the CMS management UI."""
    try:
        seed_cms_defaults_if_needed()
        contents = PageContent.objects().order_by('page', 'sortOrder')
        grouped = {}
        for c in contents:
            if c.page not in grouped:
                grouped[c.page] = []
            grouped[c.page].append(c.to_dict())
        return jsonify({
            "status": "success",
            "data": grouped
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def check_super_admin_access():
    """Validates that the current user has exclusive Super Admin authority."""
    try:
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return False, "Authentication token required."
        user = User.objects(id=current_user_id).first()
        if not user or user.role != User.ROLE_SUPER_ADMIN:
            return False, "Access denied. Only Super Admin can modify platform settings."
        return True, user
    except Exception as e:
        return False, str(e)

def update_content(section_key):
    """Update a single content entry (Super Admin only)."""
    authorized, res = check_super_admin_access()
    if not authorized:
        return jsonify({"status": "error", "message": res}), 403

    try:
        data = request.get_json(force=True) or {}
        item = PageContent.objects(sectionKey=section_key).first()
        if not item:
            return jsonify({"status": "error", "message": "Content key not found"}), 404

        if "content" in data:
            item.content = data["content"]
        if "label" in data:
            item.label = data["label"]

        item.save()
        return jsonify({"status": "success", "data": item.to_dict()}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def batch_update_content():
    """Bulk update multiple dynamic text entries (Super Admin only)."""
    authorized, res = check_super_admin_access()
    if not authorized:
        return jsonify({"status": "error", "message": res}), 403

    try:
        data = request.get_json(force=True) or {}
        updates = data.get("updates", data)
        updated_count = 0

        if isinstance(updates, dict):
            for k, v in updates.items():
                item = PageContent.objects(sectionKey=k).first()
                if item:
                    item.content = str(v)
                    item.save()
                    updated_count += 1
        elif isinstance(updates, list):
            for row in updates:
                k = row.get("sectionKey")
                v = row.get("content")
                if k and v is not None:
                    item = PageContent.objects(sectionKey=k).first()
                    if item:
                        item.content = str(v)
                        item.save()
                        updated_count += 1

        return jsonify({
            "status": "success",
            "message": f"Successfully updated {updated_count} dynamic text elements",
            "updatedCount": updated_count
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def reset_default_content():
    """Resets all dynamic headings back to system canonical defaults (Super Admin only)."""
    authorized, res = check_super_admin_access()
    if not authorized:
        return jsonify({"status": "error", "message": res}), 403

    try:
        for item in DEFAULT_PAGE_CONTENTS:
            existing = PageContent.objects(sectionKey=item["sectionKey"]).first()
            if existing:
                existing.content = item["content"]
                existing.label = item["label"]
                existing.contentType = item["contentType"]
                existing.sortOrder = item["sortOrder"]
                existing.save()
            else:
                PageContent(**item).save()

        return jsonify({
            "status": "success",
            "message": "All headings and paragraphs restored to defaults successfully"
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
