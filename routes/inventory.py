from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Item, Category, InventoryLog
from app import db
from utils.helpers import requires_role
from datetime import datetime

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/')
@login_required
@requires_role(['Admin', 'Supervisor'])
def inventory():
    items = Item.query.join(Category).all()
    categories = Category.query.all()
    low_stock_items = Item.query.filter(Item.quantity <= Item.low_stock_alert).all()
    
    return render_template('inventory/inventory.html', 
                         items=items, 
                         categories=categories,
                         low_stock_items=low_stock_items)

@inventory_bp.route('/items/new', methods=['GET', 'POST'])
@login_required
@requires_role(['Admin', 'Supervisor'])
def new_item():
    if request.method == 'POST':
        item = Item(
            name=request.form['name'],
            barcode=request.form['barcode'],
            category_id=request.form['category_id'],
            unit_price=request.form['unit_price'],
            cost_price=request.form['cost_price'],
            quantity=request.form['quantity'],
            low_stock_alert=request.form['low_stock_alert'],
            is_active=True
        )
        db.session.add(item)
        db.session.commit()
        
        # Log inventory addition
        log = InventoryLog(
            item_id=item.id,
            quantity_diff=item.quantity,
            reason='Initial stock',
            user_id=current_user.id,
            date=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Item added successfully', 'success')
        return redirect(url_for('inventory.inventory'))
    
    categories = Category.query.all()
    return render_template('inventory/new_item.html', categories=categories)

@inventory_bp.route('/items/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
@requires_role(['Admin', 'Supervisor'])
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    
    if request.method == 'POST':
        old_quantity = item.quantity
        
        item.name = request.form['name']
        item.barcode = request.form['barcode']
        item.category_id = request.form['category_id']
        item.unit_price = request.form['unit_price']
        item.cost_price = request.form['cost_price']
        item.quantity = int(request.form['quantity'])
        item.low_stock_alert = request.form['low_stock_alert']
        
        # Log quantity change if different
        if old_quantity != item.quantity:
            log = InventoryLog(
                item_id=item.id,
                quantity_diff=item.quantity - old_quantity,
                reason='Manual adjustment',
                user_id=current_user.id,
                date=datetime.utcnow()
            )
            db.session.add(log)
        
        db.session.commit()
        flash('Item updated successfully', 'success')
        return redirect(url_for('inventory.inventory'))
    
    categories = Category.query.all()
    return render_template('inventory/edit_item.html', item=item, categories=categories)

@inventory_bp.route('/items/<int:item_id>/adjust', methods=['POST'])
@login_required
@requires_role(['Admin', 'Supervisor'])
def adjust_inventory(item_id):
    item = Item.query.get_or_404(item_id)
    quantity_change = int(request.form['quantity_change'])
    reason = request.form['reason']
    
    item.quantity += quantity_change
    
    # Log the adjustment
    log = InventoryLog(
        item_id=item.id,
        quantity_diff=quantity_change,
        reason=reason,
        user_id=current_user.id,
        date=datetime.utcnow()
    )
    
    db.session.add(log)
    db.session.commit()
    
    flash('Inventory adjusted successfully', 'success')
    return redirect(url_for('inventory.inventory'))

@inventory_bp.route('/categories')
@login_required
@requires_role(['Admin', 'Supervisor'])
def categories():
    categories = Category.query.all()
    return render_template('inventory/categories.html', categories=categories)

@inventory_bp.route('/categories/new', methods=['POST'])
@login_required
@requires_role(['Admin', 'Supervisor'])
def new_category():
    category = Category(name=request.form['name'])
    db.session.add(category)
    db.session.commit()
    flash('Category added successfully', 'success')
    return redirect(url_for('inventory.categories'))

@inventory_bp.route('/logs')
@login_required
@requires_role(['Admin', 'Supervisor'])
def inventory_logs():
    logs = InventoryLog.query.order_by(InventoryLog.date.desc()).limit(100).all()
    return render_template('inventory/logs.html', logs=logs)
