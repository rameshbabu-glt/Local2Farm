"""
Unit and Integration Tests for Local2Farm
Verifies Database Models, Auth, AI Agent Tools, Analysis, and Flask Endpoints.
"""

import unittest
from datetime import datetime, timedelta
from app import create_app
from models import db, Farmer, Admin, Buyer, Market, CropPrice, SellingRequest, Recommendation
from agent.tools import (
    search_buyers,
    search_markets,
    get_crop_price,
    calculate_transport_cost,
    estimate_waste_risk,
    calculate_net_amount,
    compare_selling_options
)
from agent import Local2FarmAgent

class Local2FarmTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            from data.sample_data import seed_database
            seed_database()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_sample_seeding(self):
        """Verify initial database seed count"""
        with self.app.app_context():
            self.assertGreaterEqual(Farmer.query.count(), 1)
            self.assertGreaterEqual(Admin.query.count(), 1)
            self.assertGreaterEqual(Buyer.query.count(), 5)
            self.assertGreaterEqual(Market.query.count(), 4)
            self.assertGreaterEqual(CropPrice.query.count(), 7)

    def test_tool_functions(self):
        """Test the 7 isolated AI Agent Python tools"""
        with self.app.app_context():
            # Tool 1: search_buyers
            buyers = search_buyers('Tomato', 'Vijayawada', 1000)
            self.assertIsInstance(buyers, list)
            self.assertGreater(len(buyers), 0)

            # Tool 2: search_markets
            markets = search_markets('Tomato', 'Vijayawada')
            self.assertIsInstance(markets, list)
            self.assertGreater(len(markets), 0)

            # Tool 3: get_crop_price
            price = get_crop_price('Tomato')
            self.assertGreater(price, 0)

            # Tool 4: calculate_transport_cost
            cost_near = calculate_transport_cost(distance=10, quantity=1000)
            cost_far = calculate_transport_cost(distance=50, quantity=1000)
            self.assertGreater(cost_far, cost_near)
            self.assertGreaterEqual(cost_near, 300.0)

            # Tool 5: estimate_waste_risk
            today = datetime.now()
            d0 = today.strftime("%Y-%m-%d")
            d1 = (today + timedelta(days=1)).strftime("%Y-%m-%d")
            d5 = (today + timedelta(days=5)).strftime("%Y-%m-%d")

            risk_low = estimate_waste_risk('Tomato', 1000, d0, d1, storage_available=False)
            self.assertEqual(risk_low['level'], 'Low')

            risk_high = estimate_waste_risk('Tomato', 1000, d0, d5, storage_available=False)
            self.assertEqual(risk_high['level'], 'High')

            # Tool 6: calculate_net_amount
            fin = calculate_net_amount(quantity=1000, price_per_kg=20.0, transport_cost=500.0)
            self.assertEqual(fin['gross_amount'], 20000.0)
            self.assertEqual(fin['net_amount'], 19500.0)

            # Tool 7: compare_selling_options
            options = compare_selling_options('Tomato', 'Vijayawada', 1000, d0, d1)
            self.assertGreater(len(options), 0)
            self.assertTrue(options[0]['is_recommended'])

    def test_ai_agent_analyze(self):
        """Test full Local2Farm AI Agent workflow execution"""
        with self.app.app_context():
            agent = Local2FarmAgent()
            today = datetime.now()
            res = agent.analyze(
                crop_name='Tomato',
                location='Vijayawada',
                quantity=1000,
                harvest_date=today.strftime("%Y-%m-%d"),
                selling_date=(today + timedelta(days=1)).strftime("%Y-%m-%d"),
                storage_available=False,
                max_distance=80
            )
            self.assertIn('options', res)
            self.assertIn('best_option', res)
            self.assertIn('explanation', res)
            self.assertIn('why_this_option', res)
            self.assertIn('disclaimer', res)
            self.assertIsNotNone(res['best_option'])
            self.assertTrue(len(res['explanation']) > 20)

    def test_farmer_login_and_crop_submission(self):
        """Test farmer login session and crop selling submission"""
        # Login as demo farmer
        resp = self.client.post('/login', data={
            'role': 'farmer',
            'email': 'ramesh@farmer.com',
            'password': 'farmer123'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # Submit crop selling form
        today = datetime.now()
        harvest = today.strftime("%Y-%m-%d")
        selling = (today + timedelta(days=1)).strftime("%Y-%m-%d")

        submit_resp = self.client.post('/farmer/sell-crop', data={
            'crop_name': 'Potato',
            'quantity': '2000',
            'location': 'Vijayawada',
            'harvest_date': harvest,
            'selling_date': selling,
            'max_distance': '100',
            'storage_available': 'yes'
        }, follow_redirects=True)
        self.assertEqual(submit_resp.status_code, 200)

        # Verify request saved in db
        with self.app.app_context():
            req = SellingRequest.query.filter_by(crop_name='Potato').first()
            self.assertIsNotNone(req)
            self.assertEqual(req.quantity, 2000.0)
            self.assertGreater(len(req.recommendations), 0)

            # Test selecting option
            top_rec = req.recommendations[0].option_name
            select_resp = self.client.post(f'/farmer/select-option/{req.id}', data={
                'chosen_option': top_rec
            }, follow_redirects=True)
            self.assertEqual(select_resp.status_code, 200)

            db.session.refresh(req)
            self.assertEqual(req.selected_option, top_rec)

    def test_admin_flow(self):
        """Test administrator login, stats API, and adding a buyer"""
        # Admin login
        resp = self.client.post('/login', data={
            'role': 'admin',
            'email': 'admin@local2farm.com',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # Check chart API endpoint
        chart_resp = self.client.get('/admin/api/chart-data')
        self.assertEqual(chart_resp.status_code, 200)
        json_data = chart_resp.get_json()
        self.assertIn('crop_distribution', json_data)
        self.assertIn('avg_prices', json_data)

        # Admin add buyer
        add_b_resp = self.client.post('/admin/buyers', data={
            'action': 'add',
            'name': 'Test New Buyer Co',
            'buyer_type': 'Wholesale Mandi Trader',
            'location': 'Vijayawada',
            'crop_type': 'Tomato, Potato',
            'price_per_kg': '25.0',
            'maximum_quantity': '10000',
            'contact': '9998887776'
        }, follow_redirects=True)
        self.assertEqual(add_b_resp.status_code, 200)

        with self.app.app_context():
            new_b = Buyer.query.filter_by(name='Test New Buyer Co').first()
            self.assertIsNotNone(new_b)
            self.assertEqual(new_b.price_per_kg, 25.0)

if __name__ == '__main__':
    unittest.main()
