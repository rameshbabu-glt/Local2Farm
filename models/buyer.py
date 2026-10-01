from datetime import datetime, timezone
from models import db

class Buyer(db.Model):
    __tablename__ = 'buyers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    crop_type = db.Column(db.String(100), nullable=False)  # Comma-separated or single crop, e.g. "Tomato" or "Tomato, Potato"
    price_per_kg = db.Column(db.Float, nullable=False)
    maximum_quantity = db.Column(db.Float, nullable=False)  # in kg
    contact = db.Column(db.String(50), nullable=False)
    buyer_type = db.Column(db.String(80), nullable=False)  # e.g., Wholesale Trader, Food Processor, Local Aggregator
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'crop_type': self.crop_type,
            'price_per_kg': self.price_per_kg,
            'maximum_quantity': self.maximum_quantity,
            'contact': self.contact,
            'buyer_type': self.buyer_type
        }

    def accepts_crop(self, crop_name):
        """Check if buyer accepts given crop (case-insensitive substring/equality)"""
        if not self.crop_type:
            return False
        crops = [c.strip().lower() for c in self.crop_type.split(',')]
        return crop_name.strip().lower() in crops or crop_name.strip().lower() in self.crop_type.lower()

    def __repr__(self):
        return f'<Buyer {self.name} - {self.crop_type} @ ₹{self.price_per_kg}/kg>'
