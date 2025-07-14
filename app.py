import os
import logging
from flask import Flask, session, request, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager, current_user

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
    return User.query.get(int(user_id))

# Language support
@app.before_request
def before_request():
    # Set default language
    if 'lang' not in session:
        session['lang'] = 'en'
    g.lang = session['lang']

# Register blueprints
from routes.auth import auth_bp
from routes.orders import orders_bp
from routes.inventory import inventory_bp
from routes.customers import customers_bp
from routes.settings import settings_bp
from routes.reports import reports_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(orders_bp, url_prefix='/orders')
app.register_blueprint(inventory_bp, url_prefix='/inventory')
app.register_blueprint(customers_bp, url_prefix='/customers')
app.register_blueprint(settings_bp, url_prefix='/settings')
app.register_blueprint(reports_bp, url_prefix='/reports')

# Main dashboard route
@app.route('/')
def dashboard():
    from flask import render_template, redirect, url_for
    from flask_login import login_required
    
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    return render_template('dashboard.html')

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
    from models import User, Settings, UserRole, Language
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
    
    db.session.commit()
