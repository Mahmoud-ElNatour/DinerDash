from app import db
from flask_login import UserMixin
from datetime import datetime
from enum import Enum
from sqlalchemy import Numeric, UniqueConstraint
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin

class UserRole(Enum):
    ADMIN = 'Admin'
    SUPERVISOR = 'Supervisor'
    WAITER = 'Waiter'

class OrderType(Enum):
    DINEIN = 'DineIn'
    TAKEAWAY = 'Takeaway'
    DELIVERY = 'Delivery'

class OrderStatus(Enum):
    PENDING = 'Pending'
    CONFIRMED = 'Confirmed'
    PAID = 'Paid'
    CANCELLED = 'Cancelled'

class TableStatus(Enum):
    AVAILABLE = 'Available'
    OCCUPIED = 'Occupied'

class MembershipLevel(Enum):
    SILVER = 'Silver'
    GOLD = 'Gold'
    VIP = 'VIP'

class DiscountType(Enum):
    FIXED = 'Fixed'
    PERCENTAGE = 'Percentage'

class Language(Enum):
    EN = 'EN'
    AR = 'AR'

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String, primary_key=True)  # Changed to String for Replit Auth
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)
    
    # POS-specific fields
    full_name = db.Column(db.String(100), nullable=True)  # Made nullable for migration
    username = db.Column(db.String(50), unique=True, nullable=True)  # Made nullable for migration
    password_hash = db.Column(db.String(256), nullable=True)  # Made nullable for migration
    role = db.Column(db.Enum(UserRole), nullable=True, default=UserRole.WAITER)  # Made nullable for migration
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    orders = db.relationship('SalesOrder', backref='user', lazy=True)
    inventory_logs = db.relationship('InventoryLog', backref='user', lazy=True)

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    points = db.Column(db.Integer, default=0)
    total_spent = db.Column(Numeric(10, 2), default=0.00)
    membership = db.Column(db.Enum(MembershipLevel), default=MembershipLevel.SILVER)
    
    # Relationships
    addresses = db.relationship('CustomerAddress', backref='customer', lazy=True)
    orders = db.relationship('SalesOrder', backref='customer', lazy=True)

class CustomerAddress(db.Model):
    __tablename__ = 'customer_addresses'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    street = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text)

class Table(db.Model):
    __tablename__ = 'tables'
    
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(10), unique=True, nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum(TableStatus), default=TableStatus.AVAILABLE)
    
    # Relationships
    orders = db.relationship('SalesOrder', backref='table', lazy=True)

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    # Relationships
    items = db.relationship('Item', backref='category', lazy=True)

class Item(db.Model):
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    barcode = db.Column(db.String(50), unique=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    unit_price = db.Column(Numeric(10, 2), nullable=False)
    cost_price = db.Column(Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    low_stock_alert = db.Column(db.Integer, default=10)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    order_items = db.relationship('SalesOrderItem', backref='item', lazy=True)
    inventory_logs = db.relationship('InventoryLog', backref='item', lazy=True)

class SalesOrder(db.Model):
    __tablename__ = 'sales_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_type = db.Column(db.Enum(OrderType), nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'))
    address_id = db.Column(db.Integer, db.ForeignKey('customer_addresses.id'))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(Numeric(10, 2), nullable=False)
    discount = db.Column(Numeric(10, 2), default=0.00)
    final_total = db.Column(Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50))
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.PENDING)
    
    # Relationships
    items = db.relationship('SalesOrderItem', backref='order', lazy=True)
    bill = db.relationship('Bill', backref='order', uselist=False)

class SalesOrderItem(db.Model):
    __tablename__ = 'sales_order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('sales_orders.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(Numeric(10, 2), nullable=False)
    total = db.Column(Numeric(10, 2), nullable=False)

class Discount(db.Model):
    __tablename__ = 'discounts'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(DiscountType), nullable=False)
    value = db.Column(Numeric(10, 2), nullable=False)
    min_purchase = db.Column(Numeric(10, 2), default=0.00)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class InventoryLog(db.Model):
    __tablename__ = 'inventory_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity_diff = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Bill(db.Model):
    __tablename__ = 'bills'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('sales_orders.id'), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50), nullable=False)
    total_paid = db.Column(Numeric(10, 2), nullable=False)
    receipt_path = db.Column(db.String(200))
    currency = db.Column(db.String(10), default='USD')
    tax_applied = db.Column(Numeric(10, 2), default=0.00)
    is_printed = db.Column(db.Boolean, default=False)

class Settings(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    currency = db.Column(db.String(10), default='USD')
    tax_rate = db.Column(Numeric(5, 4), default=0.1000)
    default_lang = db.Column(db.Enum(Language), default=Language.EN)
    receipt_note = db.Column(db.Text)
