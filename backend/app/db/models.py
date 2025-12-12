from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class Dealer(Base):
    """Dealer information."""
    __tablename__ = "dealers"

    id = Column(Integer, primary_key=True, index=True)
    dealer_code = Column(String(50), unique=True, index=True)
    name = Column(String(200))
    region = Column(String(50))  # Midwest, Northeast, Southeast, West
    state = Column(String(50))
    city = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    fni_transactions = relationship("FNITransaction", back_populates="dealer")
    marketing_campaigns = relationship("MarketingCampaign", back_populates="dealer")
    service_appointments = relationship("ServiceAppointment", back_populates="dealer")
    repair_orders = relationship("RepairOrder", back_populates="dealer")


class FNITransaction(Base):
    """Finance and Insurance transactions."""
    __tablename__ = "fni_transactions"

    id = Column(Integer, primary_key=True, index=True)
    dealer_id = Column(Integer, ForeignKey("dealers.id"))
    transaction_date = Column(Date, index=True)
    vehicle_type = Column(String(50))  # New, Used
    sale_price = Column(Float)
    fni_revenue = Column(Float)
    service_contract_sold = Column(Boolean, default=False)
    service_contract_revenue = Column(Float, default=0)
    gap_insurance_sold = Column(Boolean, default=False)
    gap_insurance_revenue = Column(Float, default=0)
    finance_manager = Column(String(100))
    penetration_rate = Column(Float)  # % of deals with F&I products

    dealer = relationship("Dealer", back_populates="fni_transactions")


class Shipment(Base):
    """Logistics and shipment data."""
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(String(50), unique=True, index=True)
    carrier = Column(String(100))
    origin = Column(String(100))
    destination = Column(String(100))
    route = Column(String(200))
    scheduled_departure = Column(DateTime)
    actual_departure = Column(DateTime, nullable=True)
    scheduled_arrival = Column(DateTime)
    actual_arrival = Column(DateTime, nullable=True)
    status = Column(String(50))  # On Time, Delayed, Delivered
    delay_reason = Column(String(100), nullable=True)  # Carrier, Route, Weather
    dwell_time_hours = Column(Float, default=0)
    vehicle_count = Column(Integer)


class Plant(Base):
    """Manufacturing plant information."""
    __tablename__ = "plants"

    id = Column(Integer, primary_key=True, index=True)
    plant_code = Column(String(50), unique=True, index=True)
    name = Column(String(200))
    location = Column(String(200))
    capacity_per_day = Column(Integer)

    # Relationships
    downtime_events = relationship("PlantDowntime", back_populates="plant")


class PlantDowntime(Base):
    """Plant downtime events."""
    __tablename__ = "plant_downtime"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id"))
    event_date = Column(Date, index=True)
    line_number = Column(String(50))
    downtime_hours = Column(Float)
    reason_category = Column(String(100))  # Maintenance, Quality, Supply, Equipment
    reason_detail = Column(String(200))
    is_planned = Column(Boolean, default=False)
    supplier = Column(String(100), nullable=True)

    plant = relationship("Plant", back_populates="downtime_events")


class MarketingCampaign(Base):
    """Marketing campaign data for Invite dashboard."""
    __tablename__ = "marketing_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    dealer_id = Column(Integer, ForeignKey("dealers.id"))
    campaign_name = Column(String(200))
    campaign_type = Column(String(100))  # Service Reminder, Oil Change, Tire Rotation, etc.
    category = Column(String(50))  # Email, SMS, Direct Mail
    send_date = Column(Date, index=True)
    emails_sent = Column(Integer, default=0)
    unique_opens = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    ro_count = Column(Integer, default=0)  # Repair Orders generated
    revenue = Column(Float, default=0)
    month = Column(String(20))

    dealer = relationship("Dealer", back_populates="marketing_campaigns")


class Customer(Base):
    """Customer information for personalized experience."""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(200), index=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(200), nullable=True)
    loyalty_tier = Column(String(20), default='Silver')  # Platinum, Gold, Silver
    preferred_services = Column(Text, nullable=True)  # JSON array as string
    service_history_count = Column(Integer, default=0)
    last_visit_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    appointments = relationship("ServiceAppointment", back_populates="customer")


class ServiceAppointment(Base):
    """Service appointment data for Engage/Customer Experience Management."""
    __tablename__ = "service_appointments"

    id = Column(Integer, primary_key=True, index=True)
    dealer_id = Column(Integer, ForeignKey("dealers.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    appointment_date = Column(Date, index=True)
    appointment_time = Column(String(10))  # e.g., "7:00 AM", "7:30 AM"
    service_type = Column(String(100))  # Regular Maintenance, Full Service, Quick Service, etc.
    estimated_duration = Column(String(20), nullable=True)  # e.g., "45 min", "2 hours"
    vehicle_vin = Column(String(50), index=True)
    vehicle_year = Column(Integer)
    vehicle_make = Column(String(50))
    vehicle_model = Column(String(50))
    vehicle_mileage = Column(String(50), nullable=True)  # e.g., "35,000 mi"
    vehicle_icon_color = Column(String(10), default='blue')  # blue, red, gray
    customer_name = Column(String(200), index=True)  # Denormalized for quick access
    advisor = Column(String(100))  # Service advisor name
    secondary_contact = Column(String(200), nullable=True)
    status = Column(String(50), index=True)  # not_arrived, checked_in, in_progress, completed, cancelled
    ro_number = Column(String(50), nullable=True)  # Repair Order number
    code = Column(String(20), nullable=True)  # e.g., "T500"
    revenue = Column(Float, default=0)
    technician = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dealer = relationship("Dealer", back_populates="service_appointments")
    customer = relationship("Customer", back_populates="appointments")


class RepairOrder(Base):
    """Repair Order (RO) data for inspection dashboard."""
    __tablename__ = "repair_orders"

    id = Column(Integer, primary_key=True, index=True)
    ro_number = Column(String(50), unique=True, index=True)  # e.g., "6149706"
    dealer_id = Column(Integer, ForeignKey("dealers.id"), nullable=True)
    priority = Column(String(10))  # 1-5
    tag = Column(String(10))  # A, B, C, D, E
    promised_date = Column(Date, index=True)
    promised_time = Column(String(20))  # e.g., "8:00 pm", "W 12:00 am"
    indicator = Column(String(10), default='')  # Status indicator
    customer_name = Column(String(200))
    advisor_id = Column(String(50))  # Service advisor ID
    technician_id = Column(String(50))  # Technician ID
    metric_time = Column(String(20))  # e.g., "1:16", "00:03"
    process_time_days = Column(Integer, default=0)  # Process time in days
    status = Column(String(50), index=True)  # awaiting_dispatch, in_inspection, pending_approval, in_repair, pending_review
    ro_type = Column(String(50), default='Standard')  # Standard, Express, etc.
    shop_type = Column(String(50), default='Service')  # Service, Body Shop, etc.
    waiter = Column(String(10), default='No')  # Yes, No
    is_overdue = Column(Boolean, default=False)
    is_urgent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dealer = relationship("Dealer", back_populates="repair_orders")


class KPIMetric(Base):
    """KPI metrics for monitoring."""
    __tablename__ = "kpi_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), index=True)
    metric_value = Column(Float)
    metric_date = Column(Date, index=True)
    region = Column(String(50), nullable=True)
    dealer_id = Column(Integer, ForeignKey("dealers.id"), nullable=True)
    category = Column(String(50))  # Sales, Service, F&I, Marketing, Logistics
    target_value = Column(Float, nullable=True)
    variance = Column(Float, nullable=True)


class KPIAlert(Base):
    """Stored KPI alerts/anomalies detected by the system."""
    __tablename__ = "kpi_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(100), unique=True, index=True)  # Unique identifier for the alert
    metric_name = Column(String(100), index=True)
    current_value = Column(Float)
    previous_value = Column(Float, nullable=True)
    target_value = Column(Float, nullable=True)
    change_percent = Column(Float)
    variance = Column(Float, nullable=True)
    severity = Column(String(20), index=True)  # critical, warning, info
    message = Column(Text)
    root_cause = Column(Text, nullable=True)
    region = Column(String(50), nullable=True)
    category = Column(String(50), index=True)  # Sales, Service, F&I, Marketing, Logistics
    status = Column(String(20), default='active', index=True)  # active, dismissed, investigated
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    dismissed_at = Column(DateTime, nullable=True)
    dismissed_by = Column(String(100), nullable=True)
    investigation_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
