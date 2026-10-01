"""
Local2Farm Sample Data Seeder
Populates initial demo data for demonstration, tests, and academic viva.
Labels all data clearly as realistic DEMO DATA.
"""

from datetime import datetime, timedelta
from models import db, Farmer, Admin, Buyer, Market, CropPrice, SellingRequest, Recommendation
from agent.tools import calculate_transport_cost, estimate_waste_risk, calculate_net_amount, estimate_distance

def seed_database():
    """Initializes and seeds database with demo users, buyers, markets, prices, and sample requests."""
    
    # 1. Admin Account
    if not Admin.query.filter_by(email="admin@local2farm.com").first():
        admin = Admin(
            name="System Admin",
            email="admin@local2farm.com"
        )
        admin.set_password("admin123")
        db.session.add(admin)

    # 2. Demo Farmer Account
    demo_farmer = Farmer.query.filter_by(email="ramesh@farmer.com").first()
    if not demo_farmer:
        demo_farmer = Farmer(
            name="Ramesh Kumar",
            mobile="9876543210",
            email="ramesh@farmer.com",
            location="Vijayawada",
            district="Krishna",
            state="Andhra Pradesh"
        )
        demo_farmer.set_password("farmer123")
        db.session.add(demo_farmer)
        db.session.commit()

    # Second sample farmer
    if not Farmer.query.filter_by(email="lakshmi@farmer.com").first():
        farmer2 = Farmer(
            name="Lakshmi Devi",
            mobile="9876501234",
            email="lakshmi@farmer.com",
            location="Guntur",
            district="Guntur",
            state="Andhra Pradesh"
        )
        farmer2.set_password("farmer123")
        db.session.add(farmer2)

    # 3. Sample Buyers
    if Buyer.query.count() == 0:
        sample_buyers = [
            Buyer(
                name="Swarna Food Processing Unit",
                location="Vijayawada",
                crop_type="Tomato, Chilli",
                price_per_kg=22.0,
                maximum_quantity=5000.0,
                contact="9848011223",
                buyer_type="Food Processing Unit"
            ),
            Buyer(
                name="FreshBasket Supermarket Direct",
                location="Guntur",
                crop_type="Tomato, Onion, Potato, Carrot",
                price_per_kg=24.5,
                maximum_quantity=3000.0,
                contact="9848033445",
                buyer_type="Retail Supermarket Chain"
            ),
            Buyer(
                name="Krishna District Veg Aggregator",
                location="Vijayawada",
                crop_type="Tomato, Brinjal, Cabbage",
                price_per_kg=20.0,
                maximum_quantity=10000.0,
                contact="9848055667",
                buyer_type="Local Aggregator"
            ),
            Buyer(
                name="Andhra Agro Exports",
                location="Guntur",
                crop_type="Chilli, Onion",
                price_per_kg=52.0,
                maximum_quantity=8000.0,
                contact="9848077889",
                buyer_type="Export Trading House"
            ),
            Buyer(
                name="Sri Sai Wholesale Traders",
                location="Tenali",
                crop_type="Potato, Onion, Cabbage, Carrot",
                price_per_kg=22.5,
                maximum_quantity=6000.0,
                contact="9848099001",
                buyer_type="Wholesale Mandi Trader"
            ),
            Buyer(
                name="Amaravati Organic Farmer Co-op",
                location="Mangalagiri",
                crop_type="Tomato, Brinjal, Chilli",
                price_per_kg=23.0,
                maximum_quantity=2500.0,
                contact="9848022334",
                buyer_type="Farmer Co-operative"
            ),
            Buyer(
                name="GreenRoot Cold Chain Logistics",
                location="Vijayawada",
                crop_type="Potato, Carrot, Onion",
                price_per_kg=23.5,
                maximum_quantity=7500.0,
                contact="9848066778",
                buyer_type="Cold Chain Buyer"
            ),
        ]
        db.session.add_all(sample_buyers)

    # 4. Sample Markets
    if Market.query.count() == 0:
        sample_markets = [
            Market(
                name="Vijayawada Rythu Bazar",
                location="Vijayawada",
                crop_type="Tomato, Onion, Potato, Chilli, Brinjal, Cabbage, Carrot",
                price_per_kg=21.0,
                market_type="Rythu Bazar",
                contact="0866-2471234"
            ),
            Market(
                name="Guntur APMC Market Yard",
                location="Guntur",
                crop_type="Tomato, Chilli, Onion, Potato, Brinjal",
                price_per_kg=23.8,
                market_type="APMC Mandi",
                contact="0863-2234567"
            ),
            Market(
                name="Tenali Agricultural Market Yard",
                location="Tenali",
                crop_type="Tomato, Brinjal, Cabbage, Carrot",
                price_per_kg=20.5,
                market_type="APMC Mandi",
                contact="08644-225678"
            ),
            Market(
                name="Mangalagiri Sub-Market Yard",
                location="Mangalagiri",
                crop_type="Tomato, Onion, Chilli, Cabbage",
                price_per_kg=21.5,
                market_type="Sub-Mandi",
                contact="08645-231122"
            ),
            Market(
                name="Krishna District Terminal Market Yard",
                location="Eluru",
                crop_type="Tomato, Potato, Onion, Cabbage, Carrot",
                price_per_kg=22.5,
                market_type="Terminal Market",
                contact="08812-245566"
            )
        ]
        db.session.add_all(sample_markets)

    # 5. Sample Crop Benchmark Prices
    if CropPrice.query.count() == 0:
        today_str = datetime.now().strftime("%Y-%m-%d")
        sample_prices = [
            CropPrice(crop_name="Tomato", market_name="Vijayawada Rythu Bazar", price_per_kg=21.0, date=today_str),
            CropPrice(crop_name="Tomato", market_name="Guntur APMC Market Yard", price_per_kg=23.8, date=today_str),
            CropPrice(crop_name="Onion", market_name="Vijayawada Rythu Bazar", price_per_kg=28.0, date=today_str),
            CropPrice(crop_name="Onion", market_name="Guntur APMC Market Yard", price_per_kg=30.0, date=today_str),
            CropPrice(crop_name="Potato", market_name="Tenali Agricultural Market Yard", price_per_kg=22.0, date=today_str),
            CropPrice(crop_name="Potato", market_name="Vijayawada Rythu Bazar", price_per_kg=20.0, date=today_str),
            CropPrice(crop_name="Chilli", market_name="Guntur APMC Market Yard", price_per_kg=54.0, date=today_str),
            CropPrice(crop_name="Chilli", market_name="Amaravati Organic Farmer Co-op", price_per_kg=50.0, date=today_str),
            CropPrice(crop_name="Brinjal", market_name="Vijayawada Rythu Bazar", price_per_kg=18.5, date=today_str),
            CropPrice(crop_name="Cabbage", market_name="Tenali Agricultural Market Yard", price_per_kg=16.0, date=today_str),
            CropPrice(crop_name="Carrot", market_name="FreshBasket Supermarket Direct", price_per_kg=32.0, date=today_str),
        ]
        db.session.add_all(sample_prices)

    db.session.commit()

    # 6. Pre-seed Sample Selling Request for demonstration if none exists
    if SellingRequest.query.count() == 0 and demo_farmer:
        today = datetime.now()
        harvest = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        selling = today.strftime("%Y-%m-%d")

        sample_req = SellingRequest(
            farmer_id=demo_farmer.id,
            crop_name="Tomato",
            quantity=1000.0,
            location="Vijayawada",
            harvest_date=harvest,
            selling_date=selling,
            storage_available=False,
            max_distance=60.0,
            selected_option="Swarna Food Processing Unit",
            decision_notes="Selected nearby processor for quick payment and lower transport risk."
        )
        db.session.add(sample_req)
        db.session.flush()

        # Add sample recommendation options for this request
        rec1 = Recommendation(
            request_id=sample_req.id,
            option_name="Swarna Food Processing Unit",
            option_type="Buyer",
            contact="9848011223",
            location="Vijayawada",
            distance=6.0,
            estimated_price=22.0,
            transport_cost=372.0,
            gross_amount=22000.0,
            waste_risk="Low",
            waste_risk_details="Selling 1 day after harvest ensures peak freshness.",
            net_amount=21628.0,
            explanation="Local buyer provides dependable pricing with minimal transportation overhead and Low waste risk.",
            is_recommended=True
        )

        rec2 = Recommendation(
            request_id=sample_req.id,
            option_name="Guntur APMC Market Yard",
            option_type="Market",
            contact="0863-2234567",
            location="Guntur",
            distance=34.0,
            estimated_price=23.8,
            transport_cost=578.0,
            gross_amount=23800.0,
            waste_risk="Low",
            waste_risk_details="Fresh batch handles transit well.",
            net_amount=23222.0,
            explanation="Higher market rate, but distance requires 34 km travel.",
            is_recommended=False
        )

        rec3 = Recommendation(
            request_id=sample_req.id,
            option_name="Krishna District Veg Aggregator",
            option_type="Buyer",
            contact="9848055667",
            location="Vijayawada",
            distance=6.0,
            estimated_price=20.0,
            transport_cost=372.0,
            gross_amount=20000.0,
            waste_risk="Low",
            waste_risk_details="Immediate local pickup.",
            net_amount=19628.0,
            explanation="Fast offloading at farm gate with guaranteed intake.",
            is_recommended=False
        )

        db.session.add_all([rec1, rec2, rec3])
        db.session.commit()

    print("[Local2Farm] Sample database successfully initialized and seeded.")
