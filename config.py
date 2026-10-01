import os
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load environment variables from .env file if it exists
load_dotenv(os.path.join(BASE_DIR, '.env'))

class Config:
    """Application Configuration Settings"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'local2farm-default-secret-key-2026')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # AI Agent Configuration
    # If DEMO_MODE is True or LLM_API_KEY is missing, agent uses explainable rule engine
    DEMO_MODE = os.environ.get('DEMO_MODE', 'True').lower() in ('true', '1', 'yes')
    LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'demo')
    LLM_API_KEY = os.environ.get('LLM_API_KEY', '')
    LLM_MODEL = os.environ.get('LLM_MODEL', 'gpt-4o-mini')

    # Supported Crops for Farmers
    SUPPORTED_CROPS = [
        "Tomato",
        "Onion",
        "Potato",
        "Chilli",
        "Brinjal",
        "Cabbage",
        "Carrot"
    ]

    # Transportation Cost Parameters (Configurable)
    # Base rate per km (₹) + weight handling factor
    TRANSPORT_BASE_RATE_PER_KM = 12.0  # ₹12/km base vehicle cost
    TRANSPORT_WEIGHT_FACTOR = 0.005    # ₹0.005 per kg per km
    TRANSPORT_MIN_COST = 300.0         # Minimum delivery charge ₹300
