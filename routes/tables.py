from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from models import Table, TableStatus, SalesOrder
from app import db
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