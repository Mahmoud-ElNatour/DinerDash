from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Table, TableStatus, SalesOrder, OrderType, OrderStatus, Item, Category, SalesOrderItem
from app import db
from datetime import datetime
from decimal import Decimal
from utils.helpers import requires_role

tables_bp = Blueprint('tables', __name__)

@tables_bp.route('/')
@login_required
def table_plan():
    """Display the visual table management interface"""
    tables = Table.query.all()
    return render_template('tables/table_plan.html', tables=tables)

@tables_bp.route('/new', methods=['GET', 'POST'])
@login_required
@requires_role(['Admin', 'Supervisor'])
def new_table():
    """Create a new table"""
    if request.method == 'POST':
        table = Table(
            number=request.form['number'],
            seats=int(request.form['seats']),
            status=TableStatus.AVAILABLE
        )
        db.session.add(table)
        db.session.commit()
        flash('Table added successfully', 'success')
        return redirect(url_for('tables.table_plan'))
    
    return render_template('tables/new_table.html')

@tables_bp.route('/<int:table_id>/edit', methods=['GET', 'POST'])
@login_required
@requires_role(['Admin', 'Supervisor'])
def edit_table(table_id):
    """Edit an existing table"""
    table = Table.query.get_or_404(table_id)
    
    if request.method == 'POST':
        table.number = request.form['number']
        table.seats = int(request.form['seats'])
        db.session.commit()
        flash('Table updated successfully', 'success')
        return redirect(url_for('tables.table_plan'))
    
    return render_template('tables/edit_table.html', table=table)

@tables_bp.route('/<int:table_id>/status', methods=['POST'])
@login_required
def update_table_status(table_id):
    """Update table status via AJAX"""
    table = Table.query.get_or_404(table_id)
    new_status = request.json.get('status')
    
    if new_status in [status.value for status in TableStatus]:
        table.status = TableStatus(new_status)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Table status updated'})
    
    return jsonify({'success': False, 'message': 'Invalid status'})

@tables_bp.route('/<int:table_id>/delete', methods=['POST'])
@login_required
@requires_role(['Admin'])
def delete_table(table_id):
    """Delete a table"""
    table = Table.query.get_or_404(table_id)
    
    # Check if table has any orders
    if table.orders:
        flash('Cannot delete table with existing orders', 'error')
        return redirect(url_for('tables.table_plan'))
    
    db.session.delete(table)
    db.session.commit()
    flash('Table deleted successfully', 'success')
    return redirect(url_for('tables.table_plan'))

@tables_bp.route('/api/tables')
@login_required
def get_tables_json():
    """Get tables data as JSON for dynamic updates"""
    tables = Table.query.all()
    return jsonify([{
        'id': table.id,
        'number': table.number,
        'seats': table.seats,
        'status': table.status.value,
        'current_orders': len([order for order in table.orders if not order.payment_method])
    } for table in tables])

@tables_bp.route('/order/<int:table_id>')
@login_required
def table_order(table_id):
    """Enhanced table ordering interface"""
    table = Table.query.get_or_404(table_id)
    categories = Category.query.all()
    items = Item.query.filter_by(is_active=True).all()
    
    return render_template('tables/table_order.html', 
                         table=table, 
                         categories=categories, 
                         items=items)

@tables_bp.route('/create_order', methods=['POST'])
@login_required
def create_order():
    """Create order for table via AJAX"""
    try:
        data = request.get_json()
        table_id = data.get('table_id')
        order_type = data.get('order_type', 'DineIn')
        items = data.get('items', [])
        
        if not table_id or not items:
            return jsonify({'success': False, 'message': 'Missing required data'})
        
        # Calculate totals
        subtotal = Decimal('0')
        cart_items = []
        
        for item_data in items:
            item = Item.query.get(item_data['item_id'])
            if not item or item.quantity < item_data['quantity']:
                return jsonify({'success': False, 'message': f'Insufficient stock for {item.name if item else "unknown item"}'})
            
            item_total = item.unit_price * item_data['quantity']
            subtotal += item_total
            cart_items.append({
                'item': item,
                'quantity': item_data['quantity'],
                'total': item_total
            })
        
        # Get tax rate
        from models import Settings
        settings = Settings.query.first()
        tax_rate = settings.tax_rate if settings else Decimal('0.1')
        
        # Calculate final total
        tax_amount = subtotal * tax_rate
        final_total = subtotal + tax_amount
        
        # Create order
        order = SalesOrder(
            customer_id=None,
            user_id=current_user.id,
            order_type=OrderType.DINEIN,
            table_id=table_id,
            address_id=None,
            total=subtotal,
            discount=Decimal('0'),
            final_total=final_total,
            status=OrderStatus.CONFIRMED,
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
                price=cart_item['item'].unit_price,
                total=cart_item['total']
            )
            db.session.add(order_item)
            
            # Update inventory
            cart_item['item'].quantity -= cart_item['quantity']
        
        # Update table status
        table = Table.query.get(table_id)
        table.status = TableStatus.OCCUPIED
        
        db.session.commit()
        
        return jsonify({'success': True, 'order_id': order.id})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@tables_bp.route('/get_table_order/<int:table_id>')
@login_required
def get_table_order(table_id):
    """Get existing order for table"""
    try:
        # Find existing unpaid order for this table
        order = SalesOrder.query.filter_by(
            table_id=table_id,
            status=OrderStatus.CONFIRMED
        ).first()
        
        if not order:
            return jsonify({'success': True, 'order': None})
        
        # Get order items
        order_items = []
        for item in order.items:
            order_items.append({
                'item_id': item.item_id,
                'item_name': item.item.name,
                'quantity': item.quantity,
                'price': float(item.price),
                'total': float(item.total),
                'item_stock': item.item.quantity + item.quantity  # Available stock + what's in order
            })
        
        return jsonify({
            'success': True,
            'order': {
                'id': order.id,
                'items': order_items,
                'total': float(order.final_total)
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})