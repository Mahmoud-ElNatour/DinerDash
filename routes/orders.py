from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import current_user
from replit_auth import require_login
from models import SalesOrder, SalesOrderItem, Item, Category, Table, Customer, CustomerAddress, Settings, TableStatus, OrderType
from app import db
from datetime import datetime
from decimal import Decimal
from utils.pdf_generator import generate_receipt

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/')
@require_login
def orders_list():
    orders = SalesOrder.query.order_by(SalesOrder.date.desc()).all()
    return render_template('orders/orders_list.html', orders=orders)

@orders_bp.route('/new')
@require_login
def new_order():
    categories = Category.query.all()
    items = Item.query.filter_by(is_active=True).all()
    tables = Table.query.filter_by(status=TableStatus.AVAILABLE).all()
    customers = Customer.query.all()
    
    return render_template('orders/new_order.html', 
                         categories=categories, 
                         items=items, 
                         tables=tables,
                         customers=customers)

@orders_bp.route('/create', methods=['POST'])
@require_login
def create_order():
    try:
        # Get form data
        order_type = request.form['order_type']
        customer_id = request.form.get('customer_id')
        table_id = request.form.get('table_id')
        address_id = request.form.get('address_id')
        
        # Parse cart items from form
        cart_items = []
        for key in request.form:
            if key.startswith('item_'):
                item_id = int(key.split('_')[1])
                quantity = int(request.form[key])
                if quantity > 0:
                    item = Item.query.get(item_id)
                    if item and item.quantity >= quantity:
                        cart_items.append({
                            'item': item,
                            'quantity': quantity,
                            'price': item.unit_price,
                            'total': item.unit_price * quantity
                        })
        
        if not cart_items:
            flash('No items selected', 'error')
            return redirect(url_for('orders.new_order'))
        
        # Calculate totals
        subtotal = sum(item['total'] for item in cart_items)
        discount = Decimal(request.form.get('discount', '0'))
        
        # Get tax rate from settings
        settings = Settings.query.first()
        tax_rate = settings.tax_rate if settings else Decimal('0.1')
        
        final_total = subtotal - discount
        tax_amount = final_total * tax_rate
        final_total_with_tax = final_total + tax_amount
        
        # Create order
        order = SalesOrder(
            customer_id=customer_id if customer_id else None,
            user_id=current_user.id,
            order_type=OrderType[order_type.upper()],
            table_id=table_id if table_id else None,
            address_id=address_id if address_id else None,
            total=subtotal,
            discount=discount,
            final_total=final_total_with_tax,
            date=datetime.utcnow()
        )
        
        db.session.add(order)
        db.session.flush()  # To get the order ID
        
        # Create order items and update inventory
        for cart_item in cart_items:
            order_item = SalesOrderItem(
                order_id=order.id,
                item_id=cart_item['item'].id,
                quantity=cart_item['quantity'],
                price=cart_item['price'],
                total=cart_item['total']
            )
            db.session.add(order_item)
            
            # Update inventory
            cart_item['item'].quantity -= cart_item['quantity']
        
        # Update table status if dine-in
        if order_type == 'DineIn' and table_id:
            table = Table.query.get(table_id)
            table.status = TableStatus.OCCUPIED
        
        db.session.commit()
        
        # Store order ID in session for payment processing
        session['order_id'] = order.id
        
        return redirect(url_for('orders.order_confirmation', order_id=order.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating order: {str(e)}', 'error')
        return redirect(url_for('orders.new_order'))

@orders_bp.route('/confirmation/<int:order_id>')
@require_login
def order_confirmation(order_id):
    order = SalesOrder.query.get_or_404(order_id)
    return render_template('orders/order_confirmation.html', order=order)

@orders_bp.route('/payment/<int:order_id>')
@require_login
def payment(order_id):
    order = SalesOrder.query.get_or_404(order_id)
    return render_template('orders/payment.html', order=order)

@orders_bp.route('/process_payment/<int:order_id>', methods=['POST'])
@require_login
def process_payment(order_id):
    from models import Bill
    from utils.pdf_generator import generate_receipt
    
    order = SalesOrder.query.get_or_404(order_id)
    payment_method = request.form['payment_method']
    
    # Get settings for currency and tax
    settings = Settings.query.first()
    currency = settings.currency if settings else 'USD'
    tax_rate = settings.tax_rate if settings else Decimal('0.1')
    
    # Calculate tax
    tax_amount = order.final_total * tax_rate / (1 + tax_rate)
    
    # Create bill
    bill = Bill(
        order_id=order.id,
        payment_method=payment_method,
        total_paid=order.final_total,
        currency=currency,
        tax_applied=tax_amount,
        payment_date=datetime.utcnow()
    )
    
    # Update order with payment method
    order.payment_method = payment_method
    
    db.session.add(bill)
    db.session.commit()
    
    # Generate receipt
    receipt_path = generate_receipt(order, bill)
    bill.receipt_path = receipt_path
    db.session.commit()
    
    # Update customer points if customer exists
    if order.customer:
        points_earned = int(order.final_total / 10)  # 1 point per $10
        order.customer.points += points_earned
        order.customer.total_spent += order.final_total
        
        # Update membership level
        from models import MembershipLevel
        if order.customer.total_spent >= 1000:
            order.customer.membership = MembershipLevel.VIP
        elif order.customer.total_spent >= 500:
            order.customer.membership = MembershipLevel.GOLD
        
        db.session.commit()
    
    # Free up table if dine-in
    if order.order_type == OrderType.DINEIN and order.table:
        order.table.status = TableStatus.AVAILABLE
        db.session.commit()
    
    flash('Payment processed successfully!', 'success')
    return redirect(url_for('orders.receipt', order_id=order.id))

@orders_bp.route('/receipt/<int:order_id>')
@require_login
def receipt(order_id):
    order = SalesOrder.query.get_or_404(order_id)
    return render_template('orders/receipt.html', order=order)

@orders_bp.route('/get_item_details/<int:item_id>')
@require_login
def get_item_details(item_id):
    item = Item.query.get_or_404(item_id)
    return jsonify({
        'id': item.id,
        'name': item.name,
        'price': float(item.unit_price),
        'quantity': item.quantity
    })
