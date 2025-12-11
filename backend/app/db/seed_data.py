"""
Seed data for Cox Automotive AI Analytics Demo.
Creates realistic data with clear cause-and-effect scenarios for the three demo use cases:
1. F&I Revenue Drop in Midwest
2. Logistics Delays - Carrier/Route/Weather
3. Plant Downtime & Root Cause
"""

import random
from datetime import datetime, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import (
    Dealer, FNITransaction, Shipment, Plant, PlantDowntime,
    MarketingCampaign, ServiceAppointment, KPIMetric
)

random.seed(42)  # For reproducibility


async def seed_dealers(session: AsyncSession):
    """Seed dealer data."""
    dealers = [
        # Midwest dealers - these will show the F&I drop
        {"dealer_code": "ABC001", "name": "ABC Ford", "region": "Midwest", "state": "Michigan", "city": "Detroit"},
        {"dealer_code": "XYZ002", "name": "XYZ Nissan", "region": "Midwest", "state": "Illinois", "city": "Chicago"},
        {"dealer_code": "MTA003", "name": "Midtown Auto", "region": "Midwest", "state": "Ohio", "city": "Columbus"},
        {"dealer_code": "LAK004", "name": "Lakeside Motors", "region": "Midwest", "state": "Minnesota", "city": "Minneapolis"},
        {"dealer_code": "CEN005", "name": "Central Honda", "region": "Midwest", "state": "Indiana", "city": "Indianapolis"},
        # Northeast dealers - control group
        {"dealer_code": "NE001", "name": "Northeast Toyota", "region": "Northeast", "state": "New York", "city": "New York"},
        {"dealer_code": "NE002", "name": "Boston Auto Group", "region": "Northeast", "state": "Massachusetts", "city": "Boston"},
        {"dealer_code": "NE003", "name": "Philly Cars", "region": "Northeast", "state": "Pennsylvania", "city": "Philadelphia"},
        # Southeast dealers
        {"dealer_code": "SE001", "name": "Sunshine Motors", "region": "Southeast", "state": "Florida", "city": "Miami"},
        {"dealer_code": "SE002", "name": "Atlanta Auto", "region": "Southeast", "state": "Georgia", "city": "Atlanta"},
        # West dealers
        {"dealer_code": "W001", "name": "Pacific Honda", "region": "West", "state": "California", "city": "Los Angeles"},
        {"dealer_code": "W002", "name": "Seattle Auto", "region": "West", "state": "Washington", "city": "Seattle"},
    ]

    dealer_objects = []
    for d in dealers:
        dealer = Dealer(**d)
        session.add(dealer)
        dealer_objects.append(dealer)

    await session.commit()
    return dealer_objects


async def seed_fni_transactions(session: AsyncSession, dealers: list):
    """
    Seed F&I transactions with clear cause-and-effect.

    Scenario: F&I revenue dropped 11% in Midwest this week.
    - 65% of decline from ABC Ford, XYZ Nissan, Midtown Auto
    - Service contract penetration dropped from 39% to 27%
    - One finance manager (John Smith at ABC Ford) had a 5-point drop
    """
    today = date.today()
    finance_managers = {
        "ABC001": ["John Smith", "Sarah Johnson"],  # John Smith will show the drop
        "XYZ002": ["Mike Brown", "Lisa Davis"],
        "MTA003": ["Tom Wilson", "Amy Chen"],
        "LAK004": ["David Lee", "Emma White"],
        "CEN005": ["Chris Martin", "Rachel Green"],
        "NE001": ["James Taylor", "Nicole Adams"],
        "NE002": ["Robert Clark", "Jennifer Hall"],
        "NE003": ["William Turner", "Amanda Scott"],
        "SE001": ["Carlos Garcia", "Maria Rodriguez"],
        "SE002": ["Kevin Brooks", "Michelle Lewis"],
        "W001": ["Brian Kim", "Jessica Wong"],
        "W002": ["Andrew Miller", "Stephanie Moore"],
    }

    for dealer in dealers:
        dealer_code = dealer.dealer_code
        managers = finance_managers.get(dealer_code, ["Default Manager"])
        is_midwest = dealer.region == "Midwest"
        is_problem_dealer = dealer_code in ["ABC001", "XYZ002", "MTA003"]

        # Generate data for last 4 weeks
        for week_offset in range(4):
            week_start = today - timedelta(days=(7 * week_offset) + 7)

            for day_offset in range(7):
                transaction_date = week_start + timedelta(days=day_offset)
                if transaction_date > today:
                    continue

                # Number of transactions per day
                num_transactions = random.randint(8, 15)

                for _ in range(num_transactions):
                    manager = random.choice(managers)

                    # Base penetration rate
                    base_penetration = 0.39

                    # This week's problem for Midwest
                    is_this_week = week_offset == 0
                    is_problem_manager = manager == "John Smith" and dealer_code == "ABC001"

                    if is_midwest and is_problem_dealer and is_this_week:
                        # Drop penetration for problem dealers this week
                        base_penetration = 0.27
                        if is_problem_manager:
                            base_penetration = 0.22  # Extra drop for John Smith

                    penetration = base_penetration + random.uniform(-0.05, 0.05)
                    service_contract_sold = random.random() < penetration
                    gap_sold = random.random() < (penetration * 0.6)

                    sale_price = random.uniform(25000, 55000)
                    service_revenue = random.uniform(1500, 3000) if service_contract_sold else 0
                    gap_revenue = random.uniform(500, 1200) if gap_sold else 0
                    total_fni = service_revenue + gap_revenue

                    transaction = FNITransaction(
                        dealer_id=dealer.id,
                        transaction_date=transaction_date,
                        vehicle_type=random.choice(["New", "Used"]),
                        sale_price=round(sale_price, 2),
                        fni_revenue=round(total_fni, 2),
                        service_contract_sold=service_contract_sold,
                        service_contract_revenue=round(service_revenue, 2),
                        gap_insurance_sold=gap_sold,
                        gap_insurance_revenue=round(gap_revenue, 2),
                        finance_manager=manager,
                        penetration_rate=round(penetration, 3)
                    )
                    session.add(transaction)

    await session.commit()


async def seed_shipments(session: AsyncSession):
    """
    Seed shipment data for logistics demo.

    Scenario: 18% of shipments delayed over past 7 days.
    - 55% of delays on Carrier X (Chicago→Detroit, Dallas→Kansas City routes)
    - Only 3 weather-related delays
    - Carrier X dwell time increased from 1.2 to 3.1 hours
    """
    carriers = ["Carrier X", "Carrier Y", "Carrier Z", "Carrier Alpha"]
    routes = [
        ("Chicago", "Detroit"),
        ("Dallas", "Kansas City"),
        ("Atlanta", "Miami"),
        ("Los Angeles", "Seattle"),
        ("New York", "Boston"),
        ("Denver", "Phoenix"),
    ]
    delay_reasons = ["Carrier", "Route", "Weather"]

    today = datetime.now()

    for day_offset in range(14):  # Last 2 weeks
        ship_date = today - timedelta(days=day_offset)
        is_recent_week = day_offset < 7

        # Generate 20-30 shipments per day
        for i in range(random.randint(20, 30)):
            origin, destination = random.choice(routes)
            route_name = f"{origin} → {destination}"
            carrier = random.choice(carriers)

            # Determine if this shipment is delayed
            is_problem_route = route_name in ["Chicago → Detroit", "Dallas → Kansas City"]
            is_carrier_x = carrier == "Carrier X"

            # Calculate delay probability
            delay_prob = 0.08  # Base 8% delay rate
            if is_recent_week and is_carrier_x and is_problem_route:
                delay_prob = 0.45  # 45% delay for problem combo

            is_delayed = random.random() < delay_prob

            # Determine delay reason
            delay_reason = None
            if is_delayed:
                if is_carrier_x and is_problem_route:
                    delay_reason = "Carrier"
                elif random.random() < 0.15:  # Only ~15% weather (about 3 total)
                    delay_reason = "Weather"
                else:
                    delay_reason = random.choice(["Carrier", "Route"])

            # Dwell time - Carrier X increased from 1.2 to 3.1 hours recently
            if is_carrier_x and is_recent_week:
                dwell_time = random.uniform(2.5, 3.8)  # Increased dwell
            elif is_carrier_x:
                dwell_time = random.uniform(1.0, 1.5)  # Normal dwell
            else:
                dwell_time = random.uniform(0.8, 1.8)

            scheduled_departure = ship_date.replace(hour=random.randint(6, 12))
            actual_departure = scheduled_departure + timedelta(hours=dwell_time if is_delayed else random.uniform(0, 0.5))

            travel_hours = random.randint(4, 12)
            scheduled_arrival = scheduled_departure + timedelta(hours=travel_hours)
            delay_hours = random.uniform(2, 8) if is_delayed else 0
            actual_arrival = scheduled_arrival + timedelta(hours=delay_hours)

            shipment = Shipment(
                shipment_id=f"SHP{ship_date.strftime('%Y%m%d')}{i:04d}",
                carrier=carrier,
                origin=origin,
                destination=destination,
                route=route_name,
                scheduled_departure=scheduled_departure,
                actual_departure=actual_departure,
                scheduled_arrival=scheduled_arrival,
                actual_arrival=actual_arrival,
                status="Delayed" if is_delayed else "On Time",
                delay_reason=delay_reason,
                dwell_time_hours=round(dwell_time, 2),
                vehicle_count=random.randint(3, 12)
            )
            session.add(shipment)

    await session.commit()


async def seed_plants_and_downtime(session: AsyncSession):
    """
    Seed plant and downtime data.

    Scenario:
    - Plant A: 6.5 hours downtime (Line 3) - conveyor maintenance (3.1h) + paint defects (2.2h)
    - Plant B: 4.2 hours - component shortage from Supplier Q
    - Plant C: 2.3 hours - planned maintenance overrun
    """
    plants_data = [
        {"plant_code": "PLANT-A", "name": "Michigan Assembly Plant", "location": "Detroit, MI", "capacity_per_day": 1200},
        {"plant_code": "PLANT-B", "name": "Ohio Manufacturing", "location": "Columbus, OH", "capacity_per_day": 800},
        {"plant_code": "PLANT-C", "name": "Indiana Works", "location": "Fort Wayne, IN", "capacity_per_day": 600},
    ]

    plants = []
    for p in plants_data:
        plant = Plant(**p)
        session.add(plant)
        plants.append(plant)

    await session.commit()

    # Refresh plants to get IDs
    for plant in plants:
        await session.refresh(plant)

    today = date.today()
    this_week_start = today - timedelta(days=today.weekday())

    # Plant A downtime - Line 3 issues
    plant_a = plants[0]
    downtime_events_a = [
        {"line": "Line 3", "hours": 3.1, "category": "Maintenance", "detail": "Unplanned conveyor maintenance", "planned": False},
        {"line": "Line 3", "hours": 2.2, "category": "Quality", "detail": "Paint defects - quality hold", "planned": False},
        {"line": "Line 1", "hours": 0.8, "category": "Equipment", "detail": "Robotic arm calibration", "planned": False},
        {"line": "Line 2", "hours": 0.4, "category": "Maintenance", "detail": "Belt replacement", "planned": True},
    ]

    for event in downtime_events_a:
        downtime = PlantDowntime(
            plant_id=plant_a.id,
            event_date=this_week_start + timedelta(days=random.randint(0, 4)),
            line_number=event["line"],
            downtime_hours=event["hours"],
            reason_category=event["category"],
            reason_detail=event["detail"],
            is_planned=event["planned"],
        )
        session.add(downtime)

    # Plant B downtime - Supplier Q issues
    plant_b = plants[1]
    downtime = PlantDowntime(
        plant_id=plant_b.id,
        event_date=this_week_start + timedelta(days=2),
        line_number="Line 1",
        downtime_hours=4.2,
        reason_category="Supply",
        reason_detail="Component shortage - electronic control units",
        is_planned=False,
        supplier="Supplier Q"
    )
    session.add(downtime)

    # Plant C downtime - Planned maintenance overrun
    plant_c = plants[2]
    downtime = PlantDowntime(
        plant_id=plant_c.id,
        event_date=this_week_start + timedelta(days=1),
        line_number="Line 2",
        downtime_hours=2.3,
        reason_category="Maintenance",
        reason_detail="Planned maintenance overrun",
        is_planned=True,
    )
    session.add(downtime)

    await session.commit()


async def seed_marketing_campaigns(session: AsyncSession, dealers: list):
    """
    Seed marketing campaign data for the Invite dashboard.
    Matches the UI shown in the PDF with program performance metrics.
    """
    campaign_types = [
        ("1st Service Due", "Service Reminder"),
        ("6-Month Checkup", "Service Reminder"),
        ("A Service Due", "Maintenance"),
        ("Alignment Check", "Maintenance"),
        ("B Service Due", "Maintenance"),
        ("Battery Check", "Seasonal"),
        ("Brake Service", "Safety"),
        ("C Service Due", "Maintenance"),
        ("Cabin Air Filter", "Maintenance"),
        ("Coolant Flush", "Maintenance"),
        ("D Service Due", "Maintenance"),
        ("Declined Service Follow-up", "Follow-up"),
        ("Engine Air Filter", "Maintenance"),
        ("Express Lube", "Quick Service"),
        ("Factory Scheduled Maintenance", "Maintenance"),
        ("Multi Point Inspection Due", "Inspection"),
        ("Oil Change", "Quick Service"),
        ("Tire Rotation", "Quick Service"),
        ("Transmission Service", "Maintenance"),
        ("Winter Prep", "Seasonal"),
    ]

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    current_month_idx = datetime.now().month - 1

    for dealer in dealers:
        for campaign_name, category in campaign_types:
            # Generate data for last 6 months
            for month_offset in range(6):
                month_idx = (current_month_idx - month_offset) % 12
                month_name = months[month_idx]

                # Vary performance by campaign type
                base_emails = random.randint(800, 2500)
                open_rate = random.uniform(0.15, 0.35)
                unique_opens = int(base_emails * open_rate)
                clicks = int(unique_opens * random.uniform(0.1, 0.25))
                ro_count = int(clicks * random.uniform(0.15, 0.4))
                avg_ro_value = random.uniform(150, 450)
                revenue = ro_count * avg_ro_value

                campaign = MarketingCampaign(
                    dealer_id=dealer.id,
                    campaign_name=campaign_name,
                    campaign_type=category,
                    category="Email",
                    send_date=date(2024 if month_idx > current_month_idx else 2025, month_idx + 1, 15),
                    emails_sent=base_emails,
                    unique_opens=unique_opens,
                    clicks=clicks,
                    ro_count=ro_count,
                    revenue=round(revenue, 2),
                    month=month_name
                )
                session.add(campaign)

    await session.commit()


async def seed_kpi_metrics(session: AsyncSession, dealers: list):
    """Seed KPI metrics for monitoring dashboard."""
    today = date.today()
    metrics = [
        ("F&I Revenue", "F&I"),
        ("Service Contract Penetration", "F&I"),
        ("Gross Profit per Unit", "Sales"),
        ("Service Revenue", "Service"),
        ("Customer Satisfaction Score", "Service"),
        ("On-Time Delivery Rate", "Logistics"),
        ("Marketing ROI", "Marketing"),
        ("Email Open Rate", "Marketing"),
    ]

    for dealer in dealers:
        for day_offset in range(30):
            metric_date = today - timedelta(days=day_offset)

            for metric_name, category in metrics:
                # Base values with realistic variation
                base_values = {
                    "F&I Revenue": 2500,
                    "Service Contract Penetration": 0.39,
                    "Gross Profit per Unit": 3200,
                    "Service Revenue": 850,
                    "Customer Satisfaction Score": 4.2,
                    "On-Time Delivery Rate": 0.92,
                    "Marketing ROI": 3.5,
                    "Email Open Rate": 0.25,
                }

                base = base_values[metric_name]
                variation = base * random.uniform(-0.1, 0.1)
                value = base + variation

                # Add the regional drop for F&I in Midwest this week
                if dealer.region == "Midwest" and day_offset < 7:
                    if metric_name == "F&I Revenue":
                        value *= 0.89  # 11% drop
                    elif metric_name == "Service Contract Penetration":
                        value = 0.27 + random.uniform(-0.03, 0.03)  # Drop from 39% to 27%

                target = base_values[metric_name] * 1.05  # 5% above base
                variance = (value - target) / target * 100

                kpi = KPIMetric(
                    metric_name=metric_name,
                    metric_value=round(value, 4),
                    metric_date=metric_date,
                    region=dealer.region,
                    dealer_id=dealer.id,
                    category=category,
                    target_value=round(target, 4),
                    variance=round(variance, 2)
                )
                session.add(kpi)

    await session.commit()


async def seed_all(session: AsyncSession):
    """Run all seed functions."""
    print("Seeding dealers...")
    dealers = await seed_dealers(session)

    print("Seeding F&I transactions...")
    await seed_fni_transactions(session, dealers)

    print("Seeding shipments...")
    await seed_shipments(session)

    print("Seeding plants and downtime...")
    await seed_plants_and_downtime(session)

    print("Seeding marketing campaigns...")
    await seed_marketing_campaigns(session, dealers)

    print("Seeding KPI metrics...")
    await seed_kpi_metrics(session, dealers)

    print("✓ All seed data created successfully!")
