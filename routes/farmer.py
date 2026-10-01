"""
Local2Farm Farmer Routes
Handles farmer dashboard, crop selling form submission, AI agent invocation,
recommendation viewing, option selection, and request history.
"""

from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Farmer, Buyer, Market, SellingRequest, Recommendation
from routes.auth import farmer_required
from agent import Local2FarmAgent
from config import Config

farmer_bp = Blueprint('farmer', __name__, url_prefix='/farmer')

@farmer_bp.route('/dashboard')
@farmer_required
def dashboard():
    """Farmer Main Dashboard"""
    farmer_id = session.get('user_id')
    farmer = db.get_or_404(Farmer, farmer_id)

    total_requests = SellingRequest.query.filter_by(farmer_id=farmer.id).count()
    recent_request = SellingRequest.query.filter_by(farmer_id=farmer.id).order_by(SellingRequest.id.desc()).first()
    total_buyers = Buyer.query.count()
    total_markets = Market.query.count()

    # Get recent 5 requests
    recent_requests = SellingRequest.query.filter_by(farmer_id=farmer.id).order_by(SellingRequest.id.desc()).limit(5).all()

    return render_template(
        'farmer_dashboard.html',
        farmer=farmer,
        total_requests=total_requests,
        recent_request=recent_request,
        total_buyers=total_buyers,
        total_markets=total_markets,
        recent_requests=recent_requests
    )


@farmer_bp.route('/sell-crop', methods=['GET', 'POST'])
@farmer_required
def sell_crop():
    """Crop Selling Submission Form and AI Analysis Trigger"""
    farmer_id = session.get('user_id')
    farmer = db.get_or_404(Farmer, farmer_id)

    today = datetime.now()
    default_harvest = today.strftime("%Y-%m-%d")
    default_selling = (today + timedelta(days=1)).strftime("%Y-%m-%d")

    if request.method == 'POST':
        crop_name = request.form.get('crop_name', '').strip()
        quantity_str = request.form.get('quantity', '').strip()
        location = request.form.get('location', '').strip()
        harvest_date = request.form.get('harvest_date', '').strip()
        selling_date = request.form.get('selling_date', '').strip()
        max_distance_str = request.form.get('max_distance', '100').strip()
        storage_available = request.form.get('storage_available') == 'yes'

        # Validation
        if not all([crop_name, quantity_str, location, harvest_date, selling_date]):
            flash("Please fill in all mandatory fields.", "danger")
            return render_template(
                'sell_crop.html',
                farmer=farmer,
                crops=Config.SUPPORTED_CROPS,
                default_harvest=default_harvest,
                default_selling=default_selling
            )

        try:
            quantity = float(quantity_str)
            if quantity <= 0:
                raise ValueError()
        except ValueError:
            flash("Quantity must be a positive number.", "danger")
            return render_template(
                'sell_crop.html',
                farmer=farmer,
                crops=Config.SUPPORTED_CROPS,
                default_harvest=default_harvest,
                default_selling=default_selling
            )

        try:
            max_distance = float(max_distance_str) if max_distance_str else 100.0
        except ValueError:
            max_distance = 100.0

        # Create Selling Request Record in Database
        selling_request = SellingRequest(
            farmer_id=farmer.id,
            crop_name=crop_name,
            quantity=quantity,
            location=location,
            harvest_date=harvest_date,
            selling_date=selling_date,
            storage_available=storage_available,
            max_distance=max_distance
        )
        db.session.add(selling_request)
        db.session.flush()  # Allocates ID without final commit yet

        # Execute Local2Farm AI Agent
        agent = Local2FarmAgent()
        analysis = agent.analyze(
            crop_name=crop_name,
            location=location,
            quantity=quantity,
            harvest_date=harvest_date,
            selling_date=selling_date,
            storage_available=storage_available,
            max_distance=max_distance
        )

        # Save AI Recommendation Options
        for opt in analysis['options']:
            rec = Recommendation(
                request_id=selling_request.id,
                option_name=opt['option_name'],
                option_type=opt['option_type'],
                contact=opt.get('contact'),
                location=opt.get('location'),
                distance=opt.get('distance', 0.0),
                estimated_price=opt['price_per_kg'],
                transport_cost=opt['transport_cost'],
                gross_amount=opt['gross_amount'],
                waste_risk=opt['waste_risk'],
                waste_risk_details=opt.get('waste_risk_details'),
                net_amount=opt['net_amount'],
                explanation=opt.get('notes'),
                is_recommended=opt.get('is_recommended', False)
            )
            db.session.add(rec)

        db.session.commit()

        flash("AI Agent has analyzed your crop selling options successfully!", "success")
        return redirect(url_for('farmer.results', request_id=selling_request.id))

    return render_template(
        'sell_crop.html',
        farmer=farmer,
        crops=Config.SUPPORTED_CROPS,
        default_harvest=default_harvest,
        default_selling=default_selling
    )


@farmer_bp.route('/results/<int:request_id>')
@farmer_required
def results(request_id):
    """View AI Recommendation Results and Decision Support Analysis"""
    farmer_id = session.get('user_id')
    selling_request = SellingRequest.query.filter_by(id=request_id, farmer_id=farmer_id).first_or_404()

    recommendations = Recommendation.query.filter_by(request_id=selling_request.id).order_by(Recommendation.net_amount.desc()).all()
    recommended_option = next((r for r in recommendations if r.is_recommended), recommendations[0] if recommendations else None)

    # Re-derive explanation and structured why points
    agent = Local2FarmAgent()
    options_dict = [r.to_dict() for r in recommendations]

    explanation = None
    why_breakdown = {}
    if recommended_option:
        best_dict = recommended_option.to_dict()
        explanation = agent._generate_rule_based_explanation(
            selling_request.crop_name,
            selling_request.location,
            selling_request.quantity,
            selling_request.harvest_date,
            selling_request.selling_date,
            selling_request.storage_available,
            options_dict,
            best_dict
        )
        why_breakdown = agent._generate_why_breakdown(best_dict, options_dict)

    return render_template(
        'results.html',
        request=selling_request,
        recommendations=recommendations,
        recommended_option=recommended_option,
        explanation=explanation,
        why_breakdown=why_breakdown
    )


@farmer_bp.route('/select-option/<int:request_id>', methods=['POST'])
@farmer_required
def select_option(request_id):
    """Farmer records their chosen option (Decision Support only, no automated transaction)"""
    farmer_id = session.get('user_id')
    selling_request = SellingRequest.query.filter_by(id=request_id, farmer_id=farmer_id).first_or_404()

    chosen_option = request.form.get('chosen_option')
    notes = request.form.get('decision_notes', '')

    if chosen_option:
        selling_request.selected_option = chosen_option
        selling_request.decision_notes = notes
        db.session.commit()
        flash(
            f"You selected: '{chosen_option}'. Your preference has been saved. "
            "Please contact the buyer or market directly to coordinate your sale.",
            "success"
        )

    return redirect(url_for('farmer.results', request_id=request_id))


@farmer_bp.route('/history')
@farmer_required
def history():
    """Farmer Request History"""
    farmer_id = session.get('user_id')
    requests = SellingRequest.query.filter_by(farmer_id=farmer_id).order_by(SellingRequest.id.desc()).all()

    return render_template('history.html', requests=requests)


@farmer_bp.route('/profile', methods=['GET', 'POST'])
@farmer_required
def profile():
    """Farmer Profile View & Edit"""
    farmer_id = session.get('user_id')
    farmer = db.get_or_404(Farmer, farmer_id)

    if request.method == 'POST':
        farmer.name = request.form.get('name', farmer.name).strip()
        farmer.mobile = request.form.get('mobile', farmer.mobile).strip()
        farmer.location = request.form.get('location', farmer.location).strip()
        farmer.district = request.form.get('district', farmer.district).strip()
        farmer.state = request.form.get('state', farmer.state).strip()

        db.session.commit()
        session['user_name'] = farmer.name
        session['farmer_location'] = farmer.location
        flash("Profile updated successfully.", "success")
        return redirect(url_for('farmer.profile'))

    return render_template('profile.html', farmer=farmer)
