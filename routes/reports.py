from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import SalesOrder, Item, Customer, Bill
from app import db
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from utils.helpers import requires_role

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
@requires_role(['Admin', 'Supervisor'])
def reports():
    return render_template('reports/reports.html')

@reports_bp.route('/sales')
@login_required
@requires_role(['Admin', 'Supervisor'])
def sales_report():
    # Get date range from request
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Convert to datetime objects
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    
    # Get sales data
    orders = SalesOrder.query.filter(
        SalesOrder.date >= start_dt,
        SalesOrder.date < end_dt
    ).all()
    
    # Calculate totals
    total_sales = sum(order.final_total for order in orders)
    total_orders = len(orders)
    
    # Group by order type
    order_types = db.session.query(
        SalesOrder.order_type,
        func.count(SalesOrder.id).label('count'),
        func.sum(SalesOrder.final_total).label('total')
    ).filter(
        SalesOrder.date >= start_dt,
        SalesOrder.date < end_dt
    ).group_by(SalesOrder.order_type).all()
    
    return render_template('reports/sales_report.html', 
                         orders=orders,
                         total_sales=total_sales,
                         total_orders=total_orders,
                         order_types=order_types,
                         start_date=start_date,
                         end_date=end_date)

@reports_bp.route('/inventory')
@login_required
@requires_role(['Admin', 'Supervisor'])
def inventory_report():
    # Low stock items
    low_stock_items = Item.query.filter(Item.quantity <= Item.low_stock_alert).all()
    
    # Top selling items
    top_items = db.session.query(
        Item.name,
        func.sum(db.text('sales_order_items.quantity')).label('total_sold')
    ).join(
        db.text('sales_order_items'), Item.id == db.text('sales_order_items.item_id')
    ).group_by(Item.name).order_by(desc('total_sold')).limit(10).all()
    
    # Items with zero stock
    zero_stock_items = Item.query.filter(Item.quantity == 0).all()
    
    return render_template('reports/inventory_report.html',
                         low_stock_items=low_stock_items,
                         top_items=top_items,
                         zero_stock_items=zero_stock_items)

@reports_bp.route('/customers')
@login_required
@requires_role(['Admin', 'Supervisor'])
def customers_report():
    # Top customers by spending
    top_customers = Customer.query.order_by(desc(Customer.total_spent)).limit(10).all()
    
    # Customers by membership level
    membership_stats = db.session.query(
        Customer.membership,
        func.count(Customer.id).label('count')
    ).group_by(Customer.membership).all()
    
    # Recent customers
    recent_customers = Customer.query.order_by(desc(Customer.id)).limit(10).all()
    
    return render_template('reports/customers_report.html',
                         top_customers=top_customers,
                         membership_stats=membership_stats,
                         recent_customers=recent_customers)

@reports_bp.route('/daily_summary')
@login_required
@requires_role(['Admin', 'Supervisor'])
def daily_summary():
    today = datetime.now().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())
    
    # Today's orders
    today_orders = SalesOrder.query.filter(
        SalesOrder.date >= start_of_day,
        SalesOrder.date <= end_of_day
    ).all()
    
    # Today's totals
    today_sales = sum(order.final_total for order in today_orders)
    today_order_count = len(today_orders)
    
    # Payment methods breakdown
    payment_methods = db.session.query(
        Bill.payment_method,
        func.count(Bill.id).label('count'),
        func.sum(Bill.total_paid).label('total')
    ).join(SalesOrder).filter(
        SalesOrder.date >= start_of_day,
        SalesOrder.date <= end_of_day
    ).group_by(Bill.payment_method).all()
    
    return render_template('reports/daily_summary.html',
                         today_orders=today_orders,
                         today_sales=today_sales,
                         today_order_count=today_order_count,
                         payment_methods=payment_methods)
