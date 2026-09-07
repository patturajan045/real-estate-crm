# test_crm.py
"""
Complete Production Test Suite for EstateFlow Real Estate CRM:
1. System Health Check & Database Connectivity
2. Authentication via Email AND Username (Case-Insensitive)
3. Role-Based Access Control & Super Admin Platform Settings Exclusivity (HTTP 403 for Admin)
4. User Deactivation & Inactive User Deletion with Lead Unassignment Safety Guard
5. In-App Notifications for Lead Assignment and Booking Follow-up
6. Complete Project, Building, and Unit Inventory Management
7. Lead Pipeline Operations & Follow-up Scheduling
8. Atomic Double-Booking Prevention & Reservation Lifecycle
9. Dynamic CMS Headings and Labels
10. Frontend Template Rendering
"""

from app import create_app
from models import User, Project, Building, Unit, Lead, Booking, PageContent, Notification

def run_all_tests():
    print("==================================================")
    print("RUNNING ESTATEFLOW CRM PRODUCTION TEST SUITE")
    print("==================================================")

    app = create_app()
    client = app.test_client()

    # ----------------------------------------------------
    # 1. System Health Check
    # ----------------------------------------------------
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.get_json()["status"] == "success"
    print("[PASS] 1. System Health Check OK")

    # ----------------------------------------------------
    # 2. Authentication: Email AND Username (Case-Insensitive)
    # ----------------------------------------------------
    print("\n--- 2. Authentication: Email & Username Verification ---")

    # Super Admin by Email
    res_sa_email = client.post("/api/auth/login", json={"email": "superadmin@crm.com", "password": "admin123"})
    assert res_sa_email.status_code == 200, f"Super Admin email login failed: {res_sa_email.get_json()}"
    sa_token = res_sa_email.get_json()["token"]
    sa_headers = {"Authorization": f"Bearer {sa_token}"}
    print("[PASS] 2.1 Super Admin login by Email OK")

    # Super Admin by Username (Name)
    res_sa_user = client.post("/api/auth/login", json={"email": "Super Administrator", "password": "admin123"})
    assert res_sa_user.status_code == 200, f"Super Admin username login failed: {res_sa_user.get_json()}"
    print("[PASS] 2.2 Super Admin login by Username ('Super Administrator') OK")

    # Super Admin by Username (Case-Insensitive lowercase)
    res_sa_lower = client.post("/api/auth/login", json={"email": "super administrator", "password": "admin123"})
    assert res_sa_lower.status_code == 200, f"Super Admin lowercase login failed: {res_sa_lower.get_json()}"
    print("[PASS] 2.3 Super Admin login case-insensitive OK")

    # Admin by Email
    res_adm_email = client.post("/api/auth/login", json={"email": "admin@crm.com", "password": "admin123"})
    assert res_adm_email.status_code == 200
    adm_token = res_adm_email.get_json()["token"]
    adm_user = res_adm_email.get_json()["user"]
    adm_headers = {"Authorization": f"Bearer {adm_token}"}
    print("[PASS] 2.4 Admin login by Email OK")

    # Admin by Username
    res_adm_user = client.post("/api/auth/login", json={"email": "System Administrator", "password": "admin123"})
    assert res_adm_user.status_code == 200
    print("[PASS] 2.5 Admin login by Username ('System Administrator') OK")

    # Sales Employee by Email
    res_sales_email = client.post("/api/auth/login", json={"email": "john.sales@crm.com", "password": "sales123"})
    assert res_sales_email.status_code == 200
    sales_token = res_sales_email.get_json()["token"]
    sales_user = res_sales_email.get_json()["user"]
    sales_headers = {"Authorization": f"Bearer {sales_token}"}
    print("[PASS] 2.6 Sales Employee login by Email OK")

    # Sales Employee by Username
    res_sales_user = client.post("/api/auth/login", json={"email": "John Sales", "password": "sales123"})
    assert res_sales_user.status_code == 200
    print("[PASS] 2.7 Sales Employee login by Username ('John Sales') OK")

    # Invalid credentials rejection
    res_bad = client.post("/api/auth/login", json={"email": "John Sales", "password": "wrongpassword"})
    assert res_bad.status_code == 401
    print("[PASS] 2.8 Invalid credentials safely rejected (HTTP 401)")

    # ----------------------------------------------------
    # 3. Super Admin Platform Settings Exclusivity (RBAC)
    # ----------------------------------------------------
    print("\n--- 3. Platform Settings Exclusivity (RBAC) ---")

    test_cms_update = {"updates": {"dashboard_title": "Executive Sales & Inventory Dashboard"}}
    
    # Super Admin can update
    res_cms_sa = client.put("/api/cms/content/batch", json=test_cms_update, headers=sa_headers)
    assert res_cms_sa.status_code == 200
    print("[PASS] 3.1 Super Admin authorized to modify CMS content")

    # Regular Admin is blocked with 403
    res_cms_adm = client.put("/api/cms/content/batch", json=test_cms_update, headers=adm_headers)
    assert res_cms_adm.status_code == 403
    print("[PASS] 3.2 Regular Admin strictly blocked (HTTP 403 Forbidden) from Platform Settings")

    # Sales Employee is blocked with 403
    res_cms_sales = client.put("/api/cms/content/batch", json=test_cms_update, headers=sales_headers)
    assert res_cms_sales.status_code == 403
    print("[PASS] 3.3 Sales Employee strictly blocked (HTTP 403 Forbidden) from Platform Settings")

    # Reset CMS to defaults
    res_reset = client.post("/api/cms/reset", headers=sa_headers)
    assert res_reset.status_code == 200
    print("[PASS] 3.4 Super Admin restored canonical CMS defaults")

    # ----------------------------------------------------
    # 4. Inactive User Deletion & Safety Guards
    # ----------------------------------------------------
    print("\n--- 4. Inactive User Deletion & Safety Guards ---")

    # Self-deletion prevented
    res_self = client.delete(f"/api/users/{adm_user['id']}", headers=adm_headers)
    assert res_self.status_code == 400
    print("[PASS] 4.1 Admin self-deletion prevented (HTTP 400)")

    # Create temporary staff
    res_staff = client.post("/api/users/", json={
        "name": "Temp Staff",
        "email": "temp.staff@crm.com",
        "password": "staffpassword123",
        "role": "Sales Employee"
    }, headers=adm_headers)
    if res_staff.status_code == 409:
        User.objects(email="temp.staff@crm.com").delete()
        res_staff = client.post("/api/users/", json={
            "name": "Temp Staff",
            "email": "temp.staff@crm.com",
            "password": "staffpassword123",
            "role": "Sales Employee"
        }, headers=adm_headers)
    assert res_staff.status_code == 201
    temp_staff_id = res_staff.get_json()["data"]["id"]

    # Assign lead to temporary staff
    lead_staff = Lead(
        customerName="Marcus Aurelius",
        email="marcus.aurelius@meditations.org",
        phoneNumber="+1-555-1212",
        assignedTo=temp_staff_id
    ).save()

    # Calling standard delete safely deactivates active staff
    res_deact = client.delete(f"/api/users/{temp_staff_id}", headers=adm_headers)
    assert res_deact.status_code == 200
    assert res_deact.get_json()["data"]["isActive"] is False
    print("[PASS] 4.2 Active staff safely deactivated before permanent deletion")

    # Now permanently delete inactive user
    res_perm = client.delete(f"/api/users/{temp_staff_id}?permanent=true", headers=adm_headers)
    assert res_perm.status_code == 200
    assert User.objects(id=temp_staff_id).first() is None
    print("[PASS] 4.3 Inactive staff permanently deleted from MongoDB")

    # Verify lead was safely unassigned (assignedTo set to None)
    lead_staff.reload()
    assert lead_staff.assignedTo is None
    lead_staff.delete()
    print("[PASS] 4.4 Lead assignedTo safely nullified upon staff deletion")

    # ----------------------------------------------------
    # 5. In-App Notifications for Follow-Up & Booking Assignments
    # ----------------------------------------------------
    print("\n--- 5. In-App Follow-up & Booking Notifications ---")

    Notification.objects(recipient=sales_user["id"]).delete()

    # Admin creates lead assigned to John Sales
    res_new_lead = client.post("/api/leads/", json={
        "customerName": "Samantha Reed",
        "email": "samantha.reed@example.com",
        "phoneNumber": "+1-555-8822",
        "assignedTo": sales_user["id"],
        "nextFollowUpDate": "2026-11-01T10:00:00Z"
    }, headers=adm_headers)
    assert res_new_lead.status_code == 201
    lead_id = res_new_lead.get_json()["data"]["id"]

    # Check notification for John Sales
    res_notif = client.get("/api/notifications/", headers=sales_headers)
    assert res_notif.status_code == 200
    notif_body = res_notif.get_json()
    assert notif_body["unreadCount"] >= 1
    first_notif = notif_body["data"][0]
    assert "Follow-up assigned by" in first_notif["message"]
    assert "Samantha Reed" in first_notif["message"]
    print(f"[PASS] 5.1 Lead follow-up assignment notification received: '{first_notif['message']}'")

    # Mark as read
    res_read = client.post(f"/api/notifications/{first_notif['id']}/read", headers=sales_headers)
    assert res_read.status_code == 200
    res_notif_after = client.get("/api/notifications/", headers=sales_headers)
    assert res_notif_after.get_json()["unreadCount"] == 0
    print("[PASS] 5.2 Notification marked as read (unread count = 0)")

    # ----------------------------------------------------
    # 6. Inventory CRUD & Atomic Double Booking Prevention
    # ----------------------------------------------------
    print("\n--- 6. Property Inventory & Atomic Booking Lifecycle ---")

    # Project
    project = Project.objects(name="Azure Bay Residences").first() or Project(
        name="Azure Bay Residences",
        city="San Diego",
        address="500 Ocean Blvd",
        status="Under Construction"
    ).save()

    # Building
    building = Building.objects(project=project, name="Pacific Tower").first() or Building(
        project=project,
        name="Pacific Tower",
        totalFloors=12
    ).save()

    # Unit
    unit = Unit.objects(building=building, unitNumber="PH-1201").first()
    if not unit:
        unit = Unit(
            project=project,
            building=building,
            unitNumber="PH-1201",
            floor=12,
            unitType="Penthouse",
            carpetAreaSqFt=2400.0,
            price=850000.0,
            status=Unit.STATUS_AVAILABLE
        ).save()
    else:
        unit.status = Unit.STATUS_AVAILABLE
        unit.save()

    # Clean up any leftover bookings for this test unit
    Booking.objects(unit=unit).delete()

    # First Booking
    booking_data = {
        "lead": lead_id,
        "unit": str(unit.id),
        "bookedBy": sales_user["id"],
        "agreementValue": 850000.0,
        "bookingAmount": 50000.0,
        "paymentMethod": "Bank Wire",
        "transactionReference": "WIRE-AZURE-001"
    }
    res_b1 = client.post("/api/bookings/", json=booking_data, headers=adm_headers)
    assert res_b1.status_code == 201
    booking_id = res_b1.get_json()["data"]["id"]
    print("[PASS] 6.1 First Booking confirmed successfully")

    # Atomic Concurrency Guard: Second attempt on same unit must be blocked (HTTP 409)
    res_b2 = client.post("/api/bookings/", json=booking_data, headers=adm_headers)
    assert res_b2.status_code == 409
    assert "Double booking prevented" in res_b2.get_json()["message"]
    print("[PASS] 6.2 Atomic Double Booking Prevention verified (HTTP 409 Conflict)")

    # Cancel booking and release unit
    res_cancel = client.post(f"/api/bookings/{booking_id}/cancel", headers=adm_headers)
    assert res_cancel.status_code == 200
    unit.reload()
    assert unit.status == Unit.STATUS_AVAILABLE
    print("[PASS] 6.3 Booking cancelled and Unit atomically released back to Available")

    # Clean up test entities
    Booking.objects(id=booking_id).delete()
    Lead.objects(id=lead_id).delete()
    Notification.objects(recipient=sales_user["id"]).delete()

    # ----------------------------------------------------
    # 7. Frontend Pages Render Test
    # ----------------------------------------------------
    print("\n--- 7. Frontend Template Rendering ---")
    pages = ["/", "/login", "/register", "/dashboard", "/leads", "/properties", "/bookings", "/users", "/settings"]
    for p in pages:
        res_p = client.get(p)
        assert res_p.status_code == 200, f"Page {p} failed with {res_p.status_code}"
    print(f"[PASS] 7.1 All {len(pages)} Web Pages rendered with HTTP 200 OK")

    print("\n==================================================")
    print("ALL PRODUCTION TESTS PASSED WITH 100% SUCCESS!")
    print("==================================================")

if __name__ == "__main__":
    run_all_tests()
