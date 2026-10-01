from datetime import datetime, timezone
from models import db

class CropPrice(db.Model):
    __tablename__ = 'crop_prices'

    id = db.Column(db.Integer, primary_key=True)
    crop_name = db.Column(db.String(100), nullable=False)
    market_name = db.Column(db.String(120), nullable=False)
    price_per_kg = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(50), nullable=False)  # Date string like YYYY-MM-DD
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'crop_name': self.crop_name,
            'market_name': self.market_name,
            'price_per_kg': self.price_per_kg,
            'date': self.date
        }

    def __repr__(self):
        return f'<CropPrice {self.crop_name} @ {self.market_name}: ₹{self.price_per_kg}/kg>'
