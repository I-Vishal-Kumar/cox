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


class ServiceAppointment(Base):
    """Service appointment data."""
    __tablename__ = "service_appointments"

    id = Column(Integer, primary_key=True, index=True)
    dealer_id = Column(Integer, ForeignKey("dealers.id"))
    appointment_date = Column(Date, index=True)
    appointment_time = Column(String(10))
    service_type = Column(String(100))
    vehicle_vin = Column(String(50))
    vehicle_year = Column(Integer)
    vehicle_make = Column(String(50))
    vehicle_model = Column(String(50))
    customer_name = Column(String(200))
    status = Column(String(50))  # Scheduled, In Progress, Completed, No Show
    revenue = Column(Float, default=0)
    technician = Column(String(100), nullable=True)

    dealer = relationship("Dealer", back_populates="service_appointments")


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
