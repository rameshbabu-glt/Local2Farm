"""
Local2Farm Agent Tools
Controlled Python functions called by the AI Agent to query data,
compute transportation costs, predict waste risks, and compare selling options.
"""

from datetime import datetime
from config import Config
from models import Buyer, Market, CropPrice

# Sample distance matrix between common agricultural hubs (in km)
# Avoids requiring external Google Maps API while giving realistic distances
DISTANCE_MATRIX = {
    ("vijayawada", "vijayawada"): 6.0,
    ("vijayawada", "guntur"): 34.0,
    ("vijayawada", "tenali"): 32.0,
    ("vijayawada", "mangalagiri"): 14.0,
    ("vijayawada", "eluru"): 60.0,
    ("guntur", "guntur"): 7.0,
    ("guntur", "vijayawada"): 34.0,
    ("guntur", "tenali"): 25.0,
    ("guntur", "mangalagiri"): 22.0,
    ("tenali", "tenali"): 5.0,
    ("tenali", "guntur"): 25.0,
    ("tenali", "vijayawada"): 32.0,
}

def estimate_distance(origin, destination):
    """
    Estimate road distance in kilometers between two locations.
    Uses sample distance matrix or rule-based fallback based on location names.
    """
    if not origin or not destination:
        return 20.0

    orig_clean = origin.strip().lower()
    dest_clean = destination.strip().lower()

    if orig_clean == dest_clean:
        return 5.0  # Within same town / local buyer

    # Check known matrix
    pair = (orig_clean, dest_clean)
    if pair in DISTANCE_MATRIX:
        return DISTANCE_MATRIX[pair]

    # Partial match check
    for (loc1, loc2), dist in DISTANCE_MATRIX.items():
        if (loc1 in orig_clean and loc2 in dest_clean) or (loc2 in orig_clean and loc1 in dest_clean):
            return dist

    # General heuristic fallback (e.g. 25 km average regional travel)
    return 25.0


def search_buyers(crop_name, farmer_location=None, quantity=None):
    """
    Tool 1: Find buyers from the database who accept the given crop.
    Optionally filter by minimum required capacity if quantity is provided.
    """
    buyers = Buyer.query.all()
    matching_buyers = []

    for buyer in buyers:
        if buyer.accepts_crop(crop_name):
            # Check if buyer can handle at least partial or full quantity
            # If buyer maximum_quantity is 0 or >= quantity/2, consider viable
            distance = estimate_distance(farmer_location, buyer.location)
            matching_buyers.append({
                'id': buyer.id,
                'name': buyer.name,
                'location': buyer.location,
                'crop_type': buyer.crop_type,
                'price_per_kg': float(buyer.price_per_kg),
                'maximum_quantity': float(buyer.maximum_quantity),
                'contact': buyer.contact,
                'buyer_type': buyer.buyer_type,
                'distance': distance
            })

    return matching_buyers


def search_markets(crop_name, farmer_location=None):
    """
    Tool 2: Find markets from the database where the crop can be traded.
    """
    markets = Market.query.all()
    matching_markets = []

    for market in markets:
        if market.accepts_crop(crop_name):
            distance = estimate_distance(farmer_location, market.location)
            matching_markets.append({
                'id': market.id,
                'name': market.name,
                'location': market.location,
                'crop_type': market.crop_type,
                'price_per_kg': float(market.price_per_kg),
                'market_type': market.market_type,
                'contact': market.contact,
                'distance': distance
            })

    return matching_markets


def get_crop_price(crop_name, market_or_buyer_name=None):
    """
    Tool 3: Get current stored benchmark or latest market price for a crop.
    """
    query = CropPrice.query.filter(CropPrice.crop_name.ilike(f"%{crop_name.strip()}%"))
    if market_or_buyer_name:
        query = query.filter(CropPrice.market_name.ilike(f"%{market_or_buyer_name.strip()}%"))

    crop_price_record = query.order_by(CropPrice.id.desc()).first()
    if crop_price_record:
        return float(crop_price_record.price_per_kg)

    # Fallback to any recent price of this crop
    fallback = CropPrice.query.filter(CropPrice.crop_name.ilike(f"%{crop_name.strip()}%")).first()
    if fallback:
        return float(fallback.price_per_kg)

    # General baseline fallback
    return 20.0


def calculate_transport_cost(distance, quantity):
    """
    Tool 4: Calculate transportation cost using configurable formula.
    Formula:
      Base cost per km * distance + Weight factor * quantity * distance
      Enforces a minimum base cost (e.g. ₹300).
    """
    distance = max(1.0, float(distance))
    quantity = max(1.0, float(quantity))

    cost = (
        (distance * Config.TRANSPORT_BASE_RATE_PER_KM) +
        (distance * quantity * Config.TRANSPORT_WEIGHT_FACTOR)
    )
    return round(max(Config.TRANSPORT_MIN_COST, cost), 2)


def estimate_waste_risk(crop_name, quantity, harvest_date_str, selling_date_str, storage_available=False):
    """
    Tool 5: Estimate waste/spoilage risk based on crop perishability,
    interval between harvest and expected sale, and storage conditions.
    
    Returns a dict with 'risk' ('Low', 'Medium', 'High') and 'explanation'.
    """
    # Calculate days difference
    try:
        harvest_dt = datetime.strptime(harvest_date_str, "%Y-%m-%d")
        selling_dt = datetime.strptime(selling_date_str, "%Y-%m-%d")
        days = (selling_dt - harvest_dt).days
    except Exception:
        days = 1  # Default to next day if parse fails

    days = max(0, days)

    # Classification of perishability
    high_perishable_crops = ["tomato", "chilli", "brinjal", "cabbage", "green chilli"]
    durable_crops = ["potato", "onion", "carrot"]

    crop_clean = crop_name.strip().lower()

    if any(p in crop_clean for p in high_perishable_crops):
        # Highly perishable crops
        if days <= 1:
            risk = "Low"
            desc = f"{crop_name} is perishable, but selling within {days} day(s) keeps spoilage risk minimal."
        elif days <= 3:
            if storage_available:
                risk = "Low"
                desc = f"Selling in {days} days is manageable with available cold/ventilated storage."
            else:
                risk = "Medium"
                desc = f"{crop_name} degrades quickly after 2 days without dedicated storage."
        else:
            if storage_available:
                risk = "Medium"
                desc = f"Storage slows down spoilage for {days} days, but quality may still decline."
            else:
                risk = "High"
                desc = f"{days} days between harvest and sale without storage leads to high spoilage/weight loss risk."
    else:
        # Durable / semi-perishable crops (Potato, Onion, etc.)
        if days <= 3:
            risk = "Low"
            desc = f"{crop_name} has high shelf stability; {days} day(s) delay has negligible waste risk."
        elif days <= 7:
            if storage_available:
                risk = "Low"
                desc = f"{crop_name} stored under good conditions remains fresh over {days} days."
            else:
                risk = "Medium"
                desc = f"{days} days without protective storage may cause slight moisture or quality loss."
        else:
            if storage_available:
                risk = "Medium"
                desc = f"{crop_name} stored for {days} days has moderate risk of sprouting or shrinkage."
            else:
                risk = "High"
                desc = f"Over a week delay without storage risks significant weight and quality loss."

    return {
        'level': risk,
        'days': days,
        'details': desc
    }


def calculate_net_amount(quantity, price_per_kg, transport_cost):
    """
    Tool 6: Calculate gross revenue and estimated net amount for the farmer.
    Formula:
      gross_amount = quantity * price_per_kg
      net_amount = gross_amount - transport_cost
    """
    gross_amount = round(float(quantity) * float(price_per_kg), 2)
    net_amount = round(gross_amount - float(transport_cost), 2)
    return {
        'gross_amount': gross_amount,
        'net_amount': max(0.0, net_amount)
    }


def compare_selling_options(crop_name, location, quantity, harvest_date, selling_date, storage_available=False, max_distance=100.0):
    """
    Tool 7: Compare all available buyer and market selling options.
    Evaluates:
      - Option name & type
      - Off-take price per kg
      - Distance & Transportation cost
      - Waste risk
      - Gross and Net return
    
    Returns a sorted list of option dictionaries, evaluated and ranked.
    """
    options = []

    # 1. Search Buyers
    matching_buyers = search_buyers(crop_name, farmer_location=location, quantity=quantity)
    for b in matching_buyers:
        dist = b['distance']
        if dist > max_distance:
            continue

        transport = calculate_transport_cost(dist, quantity)
        waste_info = estimate_waste_risk(crop_name, quantity, harvest_date, selling_date, storage_available)
        finances = calculate_net_amount(quantity, b['price_per_kg'], transport)

        options.append({
            'option_name': b['name'],
            'option_type': 'Buyer',
            'subtype': b['buyer_type'],
            'contact': b['contact'],
            'location': b['location'],
            'distance': dist,
            'price_per_kg': b['price_per_kg'],
            'transport_cost': transport,
            'gross_amount': finances['gross_amount'],
            'net_amount': finances['net_amount'],
            'waste_risk': waste_info['level'],
            'waste_risk_details': waste_info['details'],
            'notes': f"Direct buyer ({b['buyer_type']}). Max capacity: {b['maximum_quantity']} kg."
        })

    # 2. Search Markets
    matching_markets = search_markets(crop_name, farmer_location=location)
    for m in matching_markets:
        dist = m['distance']
        if dist > max_distance:
            continue

        transport = calculate_transport_cost(dist, quantity)
        waste_info = estimate_waste_risk(crop_name, quantity, harvest_date, selling_date, storage_available)
        finances = calculate_net_amount(quantity, m['price_per_kg'], transport)

        options.append({
            'option_name': m['name'],
            'option_type': 'Market',
            'subtype': m['market_type'],
            'contact': m['contact'],
            'location': m['location'],
            'distance': dist,
            'price_per_kg': m['price_per_kg'],
            'transport_cost': transport,
            'gross_amount': finances['gross_amount'],
            'net_amount': finances['net_amount'],
            'waste_risk': waste_info['level'],
            'waste_risk_details': waste_info['details'],
            'notes': f"Regulated public/cooperative facility ({m['market_type']}). Open trade."
        })

    # If no exact match found, generate a baseline benchmark option from CropPrice
    if not options:
        bench_price = get_crop_price(crop_name)
        bench_dist = 15.0
        transport = calculate_transport_cost(bench_dist, quantity)
        waste_info = estimate_waste_risk(crop_name, quantity, harvest_date, selling_date, storage_available)
        finances = calculate_net_amount(quantity, bench_price, transport)

        options.append({
            'option_name': f"District APMC Mandi ({location} Region)",
            'option_type': 'Market',
            'subtype': 'General APMC Mandi',
            'contact': 'Mandi Committee Helpline',
            'location': location,
            'distance': bench_dist,
            'price_per_kg': bench_price,
            'transport_cost': transport,
            'gross_amount': finances['gross_amount'],
            'net_amount': finances['net_amount'],
            'waste_risk': waste_info['level'],
            'waste_risk_details': waste_info['details'],
            'notes': "Benchmark reference option based on district market prices."
        })

    # Rank options: primarily by Net Amount, but penalize High Waste Risk
    # Scoring metric: Net Amount with safety adjustment
    def score_option(opt):
        score = opt['net_amount']
        if opt['waste_risk'] == 'High':
            score *= 0.85  # 15% risk penalty
        elif opt['waste_risk'] == 'Medium':
            score *= 0.95  # 5% risk penalty
        return score

    options.sort(key=score_option, reverse=True)

    # Flag the top recommended option
    for i, opt in enumerate(options):
        opt['is_recommended'] = (i == 0)

    return options
