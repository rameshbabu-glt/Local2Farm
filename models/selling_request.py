from datetime import datetime, timezone
from models import db

class SellingRequest(db.Model):
    __tablename__ = 'selling_requests'

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=False)
    crop_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)  # in kg
    location = db.Column(db.String(120), nullable=False)
    harvest_date = db.Column(db.String(50), nullable=False)  # YYYY-MM-DD
    selling_date = db.Column(db.String(50), nullable=False)  # YYYY-MM-DD
    storage_available = db.Column(db.Boolean, default=False)
    max_distance = db.Column(db.Float, default=100.0)  # in km
    selected_option = db.Column(db.String(150), nullable=True)  # Farmer's chosen option
    decision_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    recommendations = db.relationship(
        'Recommendation',
        backref='request',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='Recommendation.net_amount.desc()'
    )

    def to_dict(self):
        return {
            'id': self.id,
            'farmer_id': self.farmer_id,
            'farmer_name': self.farmer.name if self.farmer else 'Unknown',
            'crop_name': self.crop_name,
            'quantity': self.quantity,
            'location': self.location,
            'harvest_date': self.harvest_date,
            'selling_date': self.selling_date,
            'storage_available': self.storage_available,
            'max_distance': self.max_distance,
            'selected_option': self.selected_option,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }

    def __repr__(self):
        return f'<SellingRequest #{self.id} {self.crop_name} - {self.quantity}kg by Farmer #{self.farmer_id}>'


class Recommendation(db.Model):
    __tablename__ = 'recommendations'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('selling_requests.id'), nullable=False)
    option_name = db.Column(db.String(150), nullable=False)
    option_type = db.Column(db.String(50), nullable=False)  # 'Buyer' or 'Market'
    contact = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(120), nullable=True)
    distance = db.Column(db.Float, default=0.0)  # in km
    estimated_price = db.Column(db.Float, nullable=False)  # price per kg (₹)
    transport_cost = db.Column(db.Float, nullable=False)  # total transport cost (₹)
    gross_amount = db.Column(db.Float, nullable=False)  # quantity * estimated_price (₹)
    waste_risk = db.Column(db.String(50), nullable=False)  # 'Low', 'Medium', 'High'
    waste_risk_details = db.Column(db.String(255), nullable=True)
    net_amount = db.Column(db.Float, nullable=False)  # gross - transport
    explanation = db.Column(db.Text, nullable=True)
    is_recommended = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'option_name': self.option_name,
            'option_type': self.option_type,
            'contact': self.contact,
            'location': self.location,
            'distance': self.distance,
            'estimated_price': self.estimated_price,
            'price_per_kg': self.estimated_price,
            'transport_cost': self.transport_cost,
            'gross_amount': self.gross_amount,
            'waste_risk': self.waste_risk,
            'waste_risk_details': self.waste_risk_details,
            'net_amount': self.net_amount,
            'explanation': self.explanation,
            'is_recommended': self.is_recommended
        }

    def __repr__(self):
        return f'<Recommendation #{self.id} for Request #{self.request_id}: {self.option_name} -> Net ₹{self.net_amount}>'
