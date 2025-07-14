import os
import logging
from flask import Flask, session, request, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager, current_user, login_required

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(user_id)

# Language support
@app.before_request
def before_request():
    # Set default language
    if 'lang' not in session:
        session['lang'] = 'en'
    g.lang = session['lang']

# Register other blueprints
from routes.auth import auth_bp
from routes.orders import orders_bp
from routes.inventory import inventory_bp
from routes.customers import customers_bp
from routes.settings import settings_bp
from routes.reports import reports_bp
from routes.tables import tables_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(orders_bp, url_prefix='/orders')
app.register_blueprint(inventory_bp, url_prefix='/inventory')
app.register_blueprint(customers_bp, url_prefix='/customers')
app.register_blueprint(settings_bp, url_prefix='/settings')
app.register_blueprint(reports_bp, url_prefix='/reports')
app.register_blueprint(tables_bp, url_prefix='/tables')

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

# Main dashboard route
@app.route('/')
def dashboard():
    from flask import render_template, redirect, url_for
    
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    return render_template('dashboard.html')

@app.route('/pos')
def pos_screen():
    from flask import render_template, redirect, url_for
    from models import Category, Item, Customer, Table, SalesOrder, TableStatus
    from datetime import datetime, timedelta
    
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    categories = Category.query.all()
    popular_items = Item.query.filter_by(is_active=True).limit(8).all()
    customers = Customer.query.all()
    available_tables = Table.query.filter_by(status=TableStatus.AVAILABLE).all()
    
    # Get recent orders from today
    today = datetime.now().date()
    recent_orders = SalesOrder.query.filter(
        SalesOrder.date >= today
    ).order_by(SalesOrder.date.desc()).limit(10).all()
    
    return render_template('pos/sales_screen.html',
                         categories=categories,
                         popular_items=popular_items,
                         customers=customers,
                         available_tables=available_tables,
                         recent_orders=recent_orders)

@app.route('/api/search_items', methods=['POST'])
def search_items():
    from flask import request, jsonify, redirect, url_for
    from models import Item, Category
    
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required'})
    
    data = request.get_json()
    query = data.get('query', '').strip()
    category_id = data.get('category')
    
    items_query = Item.query.filter_by(is_active=True)
    
    if query:
        items_query = items_query.filter(
            Item.name.ilike(f'%{query}%') | 
            Item.barcode.ilike(f'%{query}%')
        )
    
    if category_id:
        items_query = items_query.filter_by(category_id=category_id)
    
    items = items_query.limit(20).all()
    
    return jsonify({
        'success': True,
        'items': [{
            'id': item.id,
            'name': item.name,
            'unit_price': float(item.unit_price),
            'quantity': item.quantity,
            'category_name': item.category.name,
            'barcode': item.barcode
        } for item in items]
    })

@app.route('/api/add_customer', methods=['POST'])
def add_customer():
    from flask import request, jsonify, redirect, url_for
    from models import Customer, MembershipLevel
    
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required'})
    
    try:
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        
        if not name:
            return jsonify({'success': False, 'message': 'Name is required'})
        
        customer = Customer(
            name=name,
            phone=phone,
            email=email,
            membership=MembershipLevel.SILVER
        )
        
        db.session.add(customer)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
                'email': customer.email,
                'membership': customer.membership.value
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/process_sale', methods=['POST'])
def process_sale():
    from flask import request, jsonify, redirect, url_for
    from models import SalesOrder, SalesOrderItem, Item, Table, Customer, Settings, OrderStatus, OrderType, TableStatus, Bill
    from datetime import datetime
    from decimal import Decimal
    from utils.pdf_generator import generate_receipt
    
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Authentication required'})
    
    try:
        data = request.get_json()
        
        # Extract data
        customer_id = data.get('customer_id')
        order_type = data.get('order_type', 'DineIn')
        table_id = data.get('table_id')
        items = data.get('items', [])
        discount = Decimal(str(data.get('discount', 0)))
        payment_method = data.get('payment_method')
        
        if not items:
            return jsonify({'success': False, 'message': 'No items in cart'})
        
        # Calculate totals
        subtotal = Decimal('0')
        cart_items = []
        
        for item_data in items:
            item = Item.query.get(item_data['item_id'])
            if not item or item.quantity < item_data['quantity']:
                return jsonify({'success': False, 'message': f'Insufficient stock for {item.name if item else "unknown item"}'})
            
            item_total = Decimal(str(item_data['price'])) * item_data['quantity']
            subtotal += item_total
            cart_items.append({
                'item': item,
                'quantity': item_data['quantity'],
                'price': Decimal(str(item_data['price'])),
                'total': item_total
            })
        
        # Apply discount
        discounted_subtotal = subtotal - discount
        
        # Get tax rate
        settings = Settings.query.first()
        tax_rate = settings.tax_rate if settings else Decimal('0.1')
        tax_amount = discounted_subtotal * tax_rate
        final_total = discounted_subtotal + tax_amount
        
        # Create order
        order = SalesOrder(
            customer_id=customer_id,
            user_id=current_user.id,
            order_type=OrderType[order_type.upper()],
            table_id=table_id,
            total=subtotal,
            discount=discount,
            final_total=final_total,
            payment_method=payment_method,
            status=OrderStatus.PAID,
            date=datetime.utcnow()
        )
        
        db.session.add(order)
        db.session.flush()
        
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
        
        # Create bill
        bill = Bill(
            order_id=order.id,
            payment_method=payment_method,
            total_paid=final_total,
            tax_applied=tax_amount,
            payment_date=datetime.utcnow()
        )
        db.session.add(bill)
        
        # Update table status if needed
        if order_type == 'DineIn' and table_id:
            table = Table.query.get(table_id)
            if table:
                table.status = TableStatus.OCCUPIED
        
        # Update customer points if customer exists
        if customer_id:
            customer = Customer.query.get(customer_id)
            if customer:
                points_earned = int(final_total / 10)  # 1 point per $10
                customer.points += points_earned
                customer.total_spent += final_total
                
                # Update membership level
                from models import MembershipLevel
                if customer.total_spent >= 1000:
                    customer.membership = MembershipLevel.VIP
                elif customer.total_spent >= 500:
                    customer.membership = MembershipLevel.GOLD
        
        db.session.commit()
        
        # Generate receipt
        receipt_path = generate_receipt(order, bill)
        bill.receipt_path = receipt_path
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order_id': order.id,
            'receipt_url': f'/orders/receipt/{order.id}',
            'total': float(final_total)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# Language switching
@app.route('/set_language/<language>')
def set_language(language):
    from flask import redirect, request
    session['lang'] = language
    return redirect(request.referrer or '/')

with app.app_context():
    # Import models to ensure tables are created
    import models
    db.create_all()
    
    # Create default admin user if not exists
    from models import User, Settings, UserRole, Language, Table, TableStatus, Category, Item
    from werkzeug.security import generate_password_hash
    
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            full_name='System Administrator',
            username='admin',
            password_hash=generate_password_hash('admin123'),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.session.add(admin_user)
    
    # Create default settings if not exists
    if not Settings.query.first():
        default_settings = Settings(
            currency='USD',
            tax_rate=0.10,
            default_lang=Language.EN,
            receipt_note='Thank you for your visit!'
        )
        db.session.add(default_settings)
    
    # Create sample tables if none exist
    if not Table.query.first():
        sample_tables = [
            Table(number='1', seats=2, status=TableStatus.AVAILABLE),
            Table(number='2', seats=4, status=TableStatus.AVAILABLE),
            Table(number='3', seats=6, status=TableStatus.AVAILABLE),
            Table(number='4', seats=2, status=TableStatus.AVAILABLE),
            Table(number='5', seats=8, status=TableStatus.AVAILABLE),
            Table(number='6', seats=4, status=TableStatus.AVAILABLE),
        ]
        for table in sample_tables:
            db.session.add(table)
    
    # Create sample categories if none exist
    if not Category.query.first():
        sample_categories = [
            Category(name='Appetizers'),
            Category(name='Main Dishes'),
            Category(name='Desserts'),
            Category(name='Beverages'),
        ]
        for category in sample_categories:
            db.session.add(category)
    
    db.session.commit()
