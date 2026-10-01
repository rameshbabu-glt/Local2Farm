"""
Local2Farm Administrator Routes
Manages farmers, buyers, markets, crop prices, requests, and analytics (using Pandas & Chart.js).
"""

from datetime import datetime
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, Farmer, Buyer, Market, CropPrice, SellingRequest, Recommendation
from routes.auth import admin_required
from config import Config

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin Dashboard with Stats and Chart Analytics"""
    total_farmers = Farmer.query.count()
    total_buyers = Buyer.query.count()
    total_markets = Market.query.count()
    total_requests = SellingRequest.query.count()

    recent_requests = SellingRequest.query.order_by(SellingRequest.id.desc()).limit(8).all()

    # Pandas Data Processing for Analytics
    # 1. Most requested crops
    requests_query = SellingRequest.query.all()
    crop_counts = {}
    total_quantity_by_crop = {}

    if requests_query:
        req_df = pd.DataFrame([{
            'crop_name': r.crop_name,
            'quantity': r.quantity
        } for r in requests_query])

        if not req_df.empty:
            crop_counts = req_df['crop_name'].value_counts().to_dict()
            total_quantity_by_crop = req_df.groupby('crop_name')['quantity'].sum().round(1).to_dict()

    # 2. Average crop prices across buyers & markets
    prices_query = CropPrice.query.all()
    avg_prices = {}
    if prices_query:
        price_df = pd.DataFrame([{
            'crop_name': p.crop_name,
            'price': p.price_per_kg
        } for p in prices_query])

        if not price_df.empty:
            avg_prices = price_df.groupby('crop_name')['price'].mean().round(2).to_dict()

    return render_template(
        'admin_dashboard.html',
        total_farmers=total_farmers,
        total_buyers=total_buyers,
        total_markets=total_markets,
        total_requests=total_requests,
        recent_requests=recent_requests,
        crop_counts=crop_counts,
        total_quantity_by_crop=total_quantity_by_crop,
        avg_prices=avg_prices
    )


# ==================== BUYERS MANAGEMENT ====================
@admin_bp.route('/buyers', methods=['GET', 'POST'])
@admin_required
def buyers():
    """List, Add, or Edit Buyers"""
    if request.method == 'POST':
        action = request.form.get('action')
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        crop_type = request.form.get('crop_type', '').strip()
        price_per_kg = float(request.form.get('price_per_kg', 0.0))
        max_quantity = float(request.form.get('maximum_quantity', 0.0))
        contact = request.form.get('contact', '').strip()
        buyer_type = request.form.get('buyer_type', 'Wholesale Trader').strip()

        if action == 'edit':
            buyer_id = request.form.get('buyer_id')
            buyer = db.get_or_404(Buyer, buyer_id)
            buyer.name = name
            buyer.location = location
            buyer.crop_type = crop_type
            buyer.price_per_kg = price_per_kg
            buyer.maximum_quantity = max_quantity
            buyer.contact = contact
            buyer.buyer_type = buyer_type
            flash(f"Buyer '{name}' updated successfully.", "success")
        else:
            new_buyer = Buyer(
                name=name,
                location=location,
                crop_type=crop_type,
                price_per_kg=price_per_kg,
                maximum_quantity=max_quantity,
                contact=contact,
                buyer_type=buyer_type
            )
            db.session.add(new_buyer)
            flash(f"New buyer '{name}' added successfully.", "success")

        db.session.commit()
        return redirect(url_for('admin.buyers'))

    all_buyers = Buyer.query.order_by(Buyer.id.desc()).all()
    return render_template('buyers.html', buyers=all_buyers, crops=Config.SUPPORTED_CROPS)


@admin_bp.route('/buyers/delete/<int:buyer_id>', methods=['POST'])
@admin_required
def delete_buyer(buyer_id):
    """Delete a Buyer"""
    buyer = db.get_or_404(Buyer, buyer_id)
    name = buyer.name
    db.session.delete(buyer)
    db.session.commit()
    flash(f"Buyer '{name}' deleted successfully.", "info")
    return redirect(url_for('admin.buyers'))


# ==================== MARKETS MANAGEMENT ====================
@admin_bp.route('/markets', methods=['GET', 'POST'])
@admin_required
def markets():
    """List, Add, or Edit Markets"""
    if request.method == 'POST':
        action = request.form.get('action')
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        crop_type = request.form.get('crop_type', '').strip()
        price_per_kg = float(request.form.get('price_per_kg', 0.0))
        market_type = request.form.get('market_type', 'APMC Mandi').strip()
        contact = request.form.get('contact', '').strip()

        if action == 'edit':
            market_id = request.form.get('market_id')
            market = db.get_or_404(Market, market_id)
            market.name = name
            market.location = location
            market.crop_type = crop_type
            market.price_per_kg = price_per_kg
            market.market_type = market_type
            market.contact = contact
            flash(f"Market '{name}' updated successfully.", "success")
        else:
            new_market = Market(
                name=name,
                location=location,
                crop_type=crop_type,
                price_per_kg=price_per_kg,
                market_type=market_type,
                contact=contact
            )
            db.session.add(new_market)
            flash(f"New market '{name}' added successfully.", "success")

        db.session.commit()
        return redirect(url_for('admin.markets'))

    all_markets = Market.query.order_by(Market.id.desc()).all()
    return render_template('markets.html', markets=all_markets, crops=Config.SUPPORTED_CROPS)


@admin_bp.route('/markets/delete/<int:market_id>', methods=['POST'])
@admin_required
def delete_market(market_id):
    """Delete a Market"""
    market = db.get_or_404(Market, market_id)
    name = market.name
    db.session.delete(market)
    db.session.commit()
    flash(f"Market '{name}' deleted successfully.", "info")
    return redirect(url_for('admin.markets'))


# ==================== CROP PRICES MANAGEMENT ====================
@admin_bp.route('/crop-prices', methods=['GET', 'POST'])
@admin_required
def crop_prices():
    """List, Add, or Edit Benchmark Crop Prices"""
    if request.method == 'POST':
        action = request.form.get('action')
        crop_name = request.form.get('crop_name', '').strip()
        market_name = request.form.get('market_name', '').strip()
        price_per_kg = float(request.form.get('price_per_kg', 0.0))
        date_str = request.form.get('date', datetime.now().strftime("%Y-%m-%d")).strip()

        if action == 'edit':
            price_id = request.form.get('price_id')
            cp = db.get_or_404(CropPrice, price_id)
            cp.crop_name = crop_name
            cp.market_name = market_name
            cp.price_per_kg = price_per_kg
            cp.date = date_str
            flash(f"Crop price for '{crop_name}' updated successfully.", "success")
        else:
            new_cp = CropPrice(
                crop_name=crop_name,
                market_name=market_name,
                price_per_kg=price_per_kg,
                date=date_str
            )
            db.session.add(new_cp)
            flash(f"Benchmark price for '{crop_name}' added successfully.", "success")

        db.session.commit()
        return redirect(url_for('admin.crop_prices'))

    all_prices = CropPrice.query.order_by(CropPrice.id.desc()).all()
    today_str = datetime.now().strftime("%Y-%m-%d")
    return render_template(
        'crop_prices.html',
        crop_prices=all_prices,
        crops=Config.SUPPORTED_CROPS,
        today_str=today_str
    )


@admin_bp.route('/crop-prices/delete/<int:price_id>', methods=['POST'])
@admin_required
def delete_crop_price(price_id):
    """Delete a benchmark Crop Price"""
    cp = db.get_or_404(CropPrice, price_id)
    db.session.delete(cp)
    db.session.commit()
    flash("Crop price record deleted successfully.", "info")
    return redirect(url_for('admin.crop_prices'))


# ==================== FARMERS & REQUESTS VIEWS ====================
@admin_bp.route('/farmers')
@admin_required
def farmers():
    """View Registered Farmers"""
    all_farmers = Farmer.query.order_by(Farmer.id.desc()).all()
    return render_template('farmers_list.html', farmers=all_farmers)


@admin_bp.route('/requests')
@admin_required
def requests():
    """View All Selling Requests Across the System"""
    all_requests = SellingRequest.query.order_by(SellingRequest.id.desc()).all()
    return render_template('requests_list.html', requests=all_requests)


@admin_bp.route('/api/chart-data')
@admin_required
def chart_data():
    """API endpoint providing aggregated chart data for Chart.js"""
    # 1. Requests by crop
    requests_query = SellingRequest.query.all()
    crops_labels = []
    crops_counts = []
    quantities = []

    if requests_query:
        df = pd.DataFrame([{'crop': r.crop_name, 'qty': r.quantity} for r in requests_query])
        counts = df['crop'].value_counts()
        crops_labels = counts.index.tolist()
        crops_counts = counts.values.tolist()

    # 2. Average price per crop from CropPrice table
    prices_query = CropPrice.query.all()
    price_labels = []
    avg_prices = []

    if prices_query:
        pdf = pd.DataFrame([{'crop': p.crop_name, 'price': p.price_per_kg} for p in prices_query])
        grouped = pdf.groupby('crop')['price'].mean().round(2)
        price_labels = grouped.index.tolist()
        avg_prices = grouped.values.tolist()

    return jsonify({
        'crop_distribution': {
            'labels': crops_labels,
            'counts': crops_counts
        },
        'avg_prices': {
            'labels': price_labels,
            'prices': avg_prices
        }
    })
