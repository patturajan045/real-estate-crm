# models.py
from datetime import datetime
from uuid import uuid4
from mongoengine import (
    Document,
    EmbeddedDocument,
    StringField,
    EmailField,
    DateTimeField,
    FloatField,
    IntField,
    BooleanField,
    ListField,
    ReferenceField,
    EmbeddedDocumentField,
    CASCADE,
    PULL,
    NULLIFY,
)

# ==========================================
# BASE & HELPER CLASSES
# ==========================================

class BaseDocument(Document):
    """
    Abstract base document providing consistent UUID keys, 
    timestamps, and serialization across all Flask routes.
    """
    meta = {"abstract": True}

    id = StringField(primary_key=True, default=lambda: str(uuid4()))
    addedTime = DateTimeField(default=datetime.utcnow)
    updatedTime = DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        self.updatedTime = datetime.utcnow()
        return super().save(*args, **kwargs)

    def to_dict(self):
        """Standard dictionary representation for Flask jsonify() responses."""
        data = {}
        for field_name in self._fields:
            val = getattr(self, field_name)
            if isinstance(val, datetime):
                data[field_name] = val.isoformat()
            elif isinstance(val, Document):
                data[field_name] = str(val.id)
            elif isinstance(val, list):
                data[field_name] = [
                    str(item.id) if isinstance(item, Document) 
                    else item.to_dict() if hasattr(item, "to_dict") 
                    else item
                    for item in val
                ]
            elif hasattr(val, "to_dict"):
                data[field_name] = val.to_dict()
            else:
                data[field_name] = val
        return data


# ==========================================
# USER & AUTHENTICATION
# ==========================================
# USER & AUTHENTICATION
# ==========================================

class User(BaseDocument):
    meta = {
        "collection": "users",
        "indexes": ["email", "role", "isActive"]
    }

    ROLE_SUPER_ADMIN = "Super Admin"
    ROLE_ADMIN = "Admin"
    ROLE_SALES = "Sales Employee"
    ROLES = (ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_SALES)

    name = StringField(required=True, max_length=120)
    email = EmailField(required=True, unique=True)
    phoneNumber = StringField(max_length=20)
    password = StringField(required=True)  # Store hashed passwords (e.g., via Werkzeug)
    role = StringField(choices=ROLES, default=ROLE_SALES)
    isActive = BooleanField(default=True)

    def to_dict(self):
        data = super().to_dict()
        data.pop("password", None)
        return data


# ==========================================
# PROPERTY MANAGEMENT 
# ==========================================

class Project(BaseDocument):
    meta = {
        "collection": "projects",
        "indexes": ["name", "city", "status"]
    }

    STATUS_PLANNING = "Planning"
    STATUS_UNDER_CONSTRUCTION = "Under Construction"
    STATUS_READY = "Ready to Move"
    STATUS_CHOICES = (STATUS_PLANNING, STATUS_UNDER_CONSTRUCTION, STATUS_READY)

    name = StringField(required=True, unique=True, max_length=150)
    description = StringField()
    builder = StringField()
    address = StringField()
    city = StringField(required=True)
    state = StringField()
    pincode = StringField()
    status = StringField(choices=STATUS_CHOICES, default=STATUS_UNDER_CONSTRUCTION)


class Building(BaseDocument):
    meta = {
        "collection": "buildings",
        "indexes": [
            ("project", "name") 
        ]
    }

    project = ReferenceField(Project, reverse_delete_rule=CASCADE, required=True)
    name = StringField(required=True, max_length=100) 
    totalFloors = IntField(default=1, min_value=1)
    notes = StringField()

    def to_dict(self):
        data = super().to_dict()
        try:
            if self.project:
                data["projectName"] = getattr(self.project, "name", "")
        except Exception:
            data["projectName"] = ""
        return data


class Unit(BaseDocument):
    meta = {
        "collection": "units",
        "indexes": [
            ("building", "unitNumber"), 
            "project",
            "status",
            "price"
        ]
    }

    UNIT_TYPE_1BHK = "1BHK"
    UNIT_TYPE_2BHK = "2BHK"
    UNIT_TYPE_3BHK = "3BHK"
    UNIT_TYPE_4BHK = "4BHK"
    UNIT_TYPE_PENTHOUSE = "Penthouse"
    UNIT_TYPE_VILLA = "Villa"
    UNIT_TYPE_COMMERCIAL = "Commercial"
    UNIT_TYPES = (
        UNIT_TYPE_1BHK, UNIT_TYPE_2BHK, UNIT_TYPE_3BHK, 
        UNIT_TYPE_4BHK, UNIT_TYPE_PENTHOUSE, UNIT_TYPE_VILLA, UNIT_TYPE_COMMERCIAL
    )

    STATUS_AVAILABLE = "Available"
    STATUS_BLOCKED = "Blocked"      
    STATUS_BOOKED = "Booked"        
    STATUS_SOLD = "Sold"            
    STATUS_CHOICES = (STATUS_AVAILABLE, STATUS_BLOCKED, STATUS_BOOKED, STATUS_SOLD)

    project = ReferenceField(Project, reverse_delete_rule=CASCADE, required=True)
    building = ReferenceField(Building, reverse_delete_rule=CASCADE, required=True)
    unitNumber = StringField(required=True, max_length=50) 
    floor = IntField(required=True)
    unitType = StringField(choices=UNIT_TYPES, default=UNIT_TYPE_2BHK)
    carpetAreaSqFt = FloatField(required=True)
    superBuiltUpAreaSqFt = FloatField()
    price = FloatField(required=True, min_value=0.0)
    status = StringField(choices=STATUS_CHOICES, default=STATUS_AVAILABLE)

    def to_dict(self):
        data = super().to_dict()
        data["projectName"] = ""
        data["buildingName"] = ""
        try:
            if self.project:
                data["projectName"] = getattr(self.project, "name", "") or ""
        except Exception:
            data["projectName"] = ""
        try:
            if self.building:
                data["buildingName"] = getattr(self.building, "name", "") or ""
        except Exception:
            data["buildingName"] = ""
        return data


# ==========================================
# LEAD MANAGEMENT & CRM
# ==========================================

class LeadNote(EmbeddedDocument):
    id = StringField(default=lambda: str(uuid4()))
    authorId = StringField(required=True)
    authorName = StringField()
    content = StringField(required=True)
    addedTime = DateTimeField(default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "authorId": self.authorId,
            "authorName": self.authorName,
            "content": self.content,
            "addedTime": self.addedTime.isoformat() if self.addedTime else None
        }


class Lead(BaseDocument):
    meta = {
        "collection": "leads",
        "indexes": [
            "email",
            "phoneNumber",
            "stage",
            "assignedTo",
            "nextFollowUpDate",
            "-addedTime"
        ]
    }

    STAGE_NEW = "New"
    STAGE_CONTACTED = "Contacted"
    STAGE_SITE_VISIT = "Site Visit"
    STAGE_INTERESTED = "Interested"
    STAGE_NEGOTIATION = "Negotiation"
    STAGE_BOOKED = "Booked"
    STAGE_LOST = "Lost"
    STAGES = (
        STAGE_NEW, STAGE_CONTACTED, STAGE_SITE_VISIT, 
        STAGE_INTERESTED, STAGE_NEGOTIATION, STAGE_BOOKED, STAGE_LOST
    )

    customerName = StringField(required=True, max_length=120)
    email = EmailField(required=True)
    phoneNumber = StringField(required=True, max_length=20)
    address = StringField()
    city = StringField()

    stage = StringField(choices=STAGES, default=STAGE_NEW)
    source = StringField(default="Website") 
    budgetMin = FloatField(default=0.0)
    budgetMax = FloatField()

    assignedTo = ReferenceField(User, reverse_delete_rule=NULLIFY)
    nextFollowUpDate = DateTimeField()
    preferredUnitType = StringField(choices=Unit.UNIT_TYPES)
    interestedUnits = ListField(ReferenceField(Unit, reverse_delete_rule=PULL))
    notes = ListField(EmbeddedDocumentField(LeadNote), default=list)

    def to_dict(self):
        data = super().to_dict()
        data["assignedToName"] = ""
        data["assignedToEmail"] = ""
        try:
            if self.assignedTo:
                data["assignedToName"] = getattr(self.assignedTo, "name", "") or ""
                data["assignedToEmail"] = getattr(self.assignedTo, "email", "") or ""
        except Exception:
            data["assignedToName"] = ""
            data["assignedToEmail"] = ""
        return data


# ==========================================
# BOOKING SYSTEM
# ==========================================

class Booking(BaseDocument):
    meta = {
        "collection": "bookings",
        "indexes": [
            "lead",
            "bookedBy",
            "status",
            {
                "fields": ["unit"],
                "name": "unique_active_unit_booking",
                "unique": True,
                "partialFilterExpression": {"status": {"$in": ["Confirmed", "Pending"]}}
            }
        ]
    }

    STATUS_PENDING = "Pending"
    STATUS_CONFIRMED = "Confirmed"
    STATUS_CANCELLED = "Cancelled"
    STATUS_CHOICES = (STATUS_PENDING, STATUS_CONFIRMED, STATUS_CANCELLED)

    bookingNumber = StringField(unique=True, default=lambda: f"BK-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}")
    lead = ReferenceField(Lead, reverse_delete_rule=CASCADE, required=True)
    unit = ReferenceField(Unit, reverse_delete_rule=CASCADE, required=True)
    bookedBy = ReferenceField(User, reverse_delete_rule=NULLIFY, required=True)

    agreementValue = FloatField(required=True, min_value=0.0)
    bookingAmount = FloatField(required=True, min_value=0.0)
    paymentMethod = StringField() 
    transactionReference = StringField()
    status = StringField(choices=STATUS_CHOICES, default=STATUS_CONFIRMED)
    cancellationReason = StringField()
    bookingDate = DateTimeField(default=datetime.utcnow)

    def to_dict(self):
        data = super().to_dict()
        data["leadName"] = ""
        data["leadPhone"] = ""
        data["leadEmail"] = ""
        data["unitNumber"] = ""
        data["unitType"] = ""
        data["buildingName"] = ""
        data["projectName"] = ""
        data["bookedByName"] = ""
        try:
            if self.lead:
                data["leadName"] = getattr(self.lead, "customerName", "") or ""
                data["leadPhone"] = getattr(self.lead, "phoneNumber", "") or ""
                data["leadEmail"] = getattr(self.lead, "email", "") or ""
        except Exception:
            pass
        try:
            if self.unit:
                data["unitNumber"] = getattr(self.unit, "unitNumber", "") or ""
                data["unitType"] = getattr(self.unit, "unitType", "") or ""
                if getattr(self.unit, "building", None):
                    data["buildingName"] = getattr(self.unit.building, "name", "") or ""
                if getattr(self.unit, "project", None):
                    data["projectName"] = getattr(self.unit.project, "name", "") or ""
        except Exception:
            pass
        try:
            if self.bookedBy:
                data["bookedByName"] = getattr(self.bookedBy, "name", "") or ""
        except Exception:
            pass
        return data


# ==========================================
# DYNAMIC PAGE CONTENT & HEADINGS (CMS)
# ==========================================

class PageContent(BaseDocument):
    meta = {
        "collection": "page_contents",
        "indexes": ["page", "sectionKey"]
    }

    page = StringField(required=True)  # 'login', 'register', 'dashboard', 'leads', 'properties', 'bookings', 'users', 'settings'
    sectionKey = StringField(required=True, unique=True)  # e.g. 'dashboard_title', 'leads_subtitle'
    label = StringField(required=True)  # Human-readable label in admin editor
    content = StringField(required=True)  # Heading / subtitle / paragraph text
    contentType = StringField(default="heading")  # 'title', 'subtitle', 'heading', 'paragraph', 'notice'
    sortOrder = IntField(default=0)

    def to_dict(self):
        return {
            "id": str(self.id),
            "page": self.page,
            "sectionKey": self.sectionKey,
            "label": self.label,
            "content": self.content,
            "contentType": self.contentType,
            "sortOrder": self.sortOrder
        }


# ==========================================
# IN-APP NOTIFICATIONS
# ==========================================

class Notification(BaseDocument):
    meta = {
        "collection": "notifications",
        "indexes": ["recipient", "isRead", "-createdTime"]
    }

    recipient = ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    sender = ReferenceField(User, reverse_delete_rule=NULLIFY)
    senderName = StringField(default="Administrator")
    title = StringField(required=True)
    message = StringField(required=True)
    entityType = StringField(default="lead")  # "lead" or "booking"
    entityId = StringField()
    isRead = BooleanField(default=False)
    createdTime = DateTimeField(default=datetime.utcnow)

    def to_dict(self):
        data = super().to_dict()
        data["senderName"] = self.senderName or (getattr(self.sender, "name", "Administrator") if self.sender else "Administrator")
        data["timeAgo"] = self.createdTime.strftime("%b %d, %I:%M %p") if self.createdTime else ""
        return data