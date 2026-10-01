from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.farmer import Farmer, Admin
from models.buyer import Buyer
from models.market import Market
from models.crop import CropPrice
from models.selling_request import SellingRequest, Recommendation

__all__ = [
    'db',
    'Farmer',
    'Admin',
    'Buyer',
    'Market',
    'CropPrice',
    'SellingRequest',
    'Recommendation'
]
