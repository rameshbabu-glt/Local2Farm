from datetime import datetime, timezone
from models import db

class Market(db.Model):
    __tablename__ = 'markets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    crop_type = db.Column(db.String(100), nullable=False)  # e.g., "Tomato" or "All Vegetables"
    price_per_kg = db.Column(db.Float, nullable=False)
    market_type = db.Column(db.String(80), nullable=False)  # e.g., APMC Mandi, Rythu Bazar, Terminal Market
    contact = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'crop_type': self.crop_type,
            'price_per_kg': self.price_per_kg,
            'market_type': self.market_type,
            'contact': self.contact
        }

    def accepts_crop(self, crop_name):
        """Check if market trades the given crop"""
        if not self.crop_type:
            return False
        if 'all' in self.crop_type.lower():
            return True
        crops = [c.strip().lower() for c in self.crop_type.split(',')]
        return crop_name.strip().lower() in crops or crop_name.strip().lower() in self.crop_type.lower()

    def __repr__(self):
        return f'<Market {self.name} - {self.location} @ ₹{self.price_per_kg}/kg>'
