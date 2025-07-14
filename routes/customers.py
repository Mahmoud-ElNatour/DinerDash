from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from models import Customer, CustomerAddress, MembershipLevel
from app import db
from utils.helpers import requires_role

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/')
@login_required
def customers():
    customers = Customer.query.all()
    return render_template('customers/customers.html', customers=customers)

@customers_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_customer():
    if request.method == 'POST':
        customer = Customer(
            name=request.form['name'],
            phone=request.form['phone'],
            email=request.form['email'],
            points=int(request.form.get('points', 0)),
            total_spent=0,
            membership=MembershipLevel[request.form.get('membership', 'SILVER').upper()]
        )
        db.session.add(customer)
        db.session.commit()
        flash('Customer added successfully', 'success')
        return redirect(url_for('customers.customers'))
    
    return render_template('customers/new_customer.html')

@customers_bp.route('/<int:customer_id>')
@login_required
def customer_detail(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return render_template('customers/customer_detail.html', customer=customer)

@customers_bp.route('/<int:customer_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    if request.method == 'POST':
        customer.name = request.form['name']
        customer.phone = request.form['phone']
        customer.email = request.form['email']
        db.session.commit()
        flash('Customer updated successfully', 'success')
        return redirect(url_for('customers.customer_detail', customer_id=customer.id))
    
    return render_template('customers/edit_customer.html', customer=customer)

@customers_bp.route('/<int:customer_id>/addresses')
@login_required
def customer_addresses(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return render_template('customers/addresses.html', customer=customer)

@customers_bp.route('/<int:customer_id>/addresses/new', methods=['POST'])
@login_required
def new_address(customer_id):
    address = CustomerAddress(
        customer_id=customer_id,
        street=request.form['street'],
        city=request.form['city'],
        notes=request.form['notes']
    )
    db.session.add(address)
    db.session.commit()
    flash('Address added successfully', 'success')
    return redirect(url_for('customers.customer_addresses', customer_id=customer_id))

@customers_bp.route('/<int:customer_id>/points', methods=['POST'])
@login_required
@requires_role(['Admin', 'Supervisor'])
def adjust_points(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    points_change = int(request.form['points_change'])
    customer.points += points_change
    db.session.commit()
    flash('Points adjusted successfully', 'success')
    return redirect(url_for('customers.customer_detail', customer_id=customer.id))

@customers_bp.route('/search')
@login_required
def search_customers():
    query = request.args.get('q', '')
    customers = Customer.query.filter(
        Customer.name.contains(query) | 
        Customer.phone.contains(query) | 
        Customer.email.contains(query)
    ).limit(10).all()
    
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'phone': c.phone,
        'email': c.email,
        'points': c.points
    } for c in customers])

@customers_bp.route('/<int:customer_id>/addresses/list')
@login_required
def get_customer_addresses(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    addresses = [{
        'id': addr.id,
        'street': addr.street,
        'city': addr.city,
        'notes': addr.notes
    } for addr in customer.addresses]
    
    return jsonify(addresses)
