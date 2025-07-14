from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import Settings, Discount
from app import db
from utils.helpers import requires_role
from datetime import datetime

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/')
@login_required
@requires_role(['Admin', 'Supervisor'])
def settings():
    settings = Settings.query.first()
    if not settings:
        settings = Settings(
            currency='USD',
            tax_rate=0.10,
            default_lang='EN',
            receipt_note='Thank you for your visit!'
        )
        db.session.add(settings)
        db.session.commit()
    
    return render_template('settings/settings.html', settings=settings)

@settings_bp.route('/update', methods=['POST'])
@login_required
@requires_role(['Admin', 'Supervisor'])
def update_settings():
    settings = Settings.query.first()
    if not settings:
        settings = Settings()
        db.session.add(settings)
    
    settings.currency = request.form['currency']
    settings.tax_rate = float(request.form['tax_rate'])
    settings.default_lang = request.form['default_lang']
    settings.receipt_note = request.form['receipt_note']
    
    db.session.commit()
    flash('Settings updated successfully', 'success')
    return redirect(url_for('settings.settings'))

@settings_bp.route('/discounts')
@login_required
@requires_role(['Admin', 'Supervisor'])
def discounts():
    discounts = Discount.query.all()
    return render_template('settings/discounts.html', discounts=discounts)

@settings_bp.route('/discounts/new', methods=['GET', 'POST'])
@login_required
@requires_role(['Admin', 'Supervisor'])
def new_discount():
    if request.method == 'POST':
        discount = Discount(
            type=request.form['type'],
            value=float(request.form['value']),
            min_purchase=float(request.form['min_purchase']),
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d'),
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d'),
            is_active=True
        )
        db.session.add(discount)
        db.session.commit()
        flash('Discount created successfully', 'success')
        return redirect(url_for('settings.discounts'))
    
    return render_template('settings/new_discount.html')

@settings_bp.route('/discounts/<int:discount_id>/toggle')
@login_required
@requires_role(['Admin', 'Supervisor'])
def toggle_discount(discount_id):
    discount = Discount.query.get_or_404(discount_id)
    discount.is_active = not discount.is_active
    db.session.commit()
    flash(f'Discount {"activated" if discount.is_active else "deactivated"} successfully', 'success')
    return redirect(url_for('settings.discounts'))
