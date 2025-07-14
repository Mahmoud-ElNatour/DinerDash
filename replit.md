# Diner POS System

## Overview

This is a comprehensive Point of Sale (POS) system for a diner built with Python Flask and SQLAlchemy. The system supports multiple order types (dine-in, takeaway, delivery), inventory management, customer loyalty programs, and multi-language support (English/Arabic).

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL (configurable via DATABASE_URL environment variable)
- **Authentication**: Flask-Login with role-based access control
- **Session Management**: Flask sessions with server-side storage
- **Templating**: Jinja2 templates with Bootstrap for responsive UI

### Frontend Architecture
- **UI Framework**: Bootstrap 5 with custom CSS
- **JavaScript**: Vanilla JavaScript for cart management and POS functionality
- **Responsive Design**: Mobile-first approach with RTL support for Arabic
- **Icons**: Font Awesome for consistent iconography

### Database Design
- **User Management**: Role-based system (Admin, Supervisor, Waiter)
- **Order Management**: Support for dine-in, takeaway, and delivery orders
- **Inventory Tracking**: Real-time stock management with low-stock alerts
- **Customer Management**: Loyalty points and membership levels
- **Settings**: Configurable tax rates, currency, and system preferences

## Key Components

### Authentication & Authorization
- **Username/Password Authentication**: Traditional login system with Flask-Login
- Password hashing with Werkzeug security utilities
- Role-based access control with decorator functions
- User roles: Admin (full access), Supervisor (limited admin), Waiter (order management)
- Default admin account: username=admin, password=admin123
- Session management with Flask sessions

### Professional POS System (IRS-Style)
- **Professional Sales Screen**: Three-panel layout inspired by IRS POS system
- **Left Panel**: Product search, category filtering, quick access items
- **Center Panel**: Shopping cart with real-time calculations and payment processing
- **Right Panel**: Customer management, order info, and recent transactions
- **Advanced Features**: Barcode scanning support, customer loyalty points, membership levels
- **Payment Processing**: Multiple payment methods (cash, card) with change calculation
- **Real-time Updates**: Live inventory checking, automatic stock deduction
- **Customer Management**: Quick customer addition, loyalty tracking, membership benefits

### Order Management System
- Multi-type order support (dine-in with table assignment, takeaway, delivery)
- **Enhanced Table Ordering**: Split-screen interface with menu selection and cart management
- Real-time cart management with JavaScript
- Order status tracking (Pending, Confirmed, Paid, Cancelled)
- Order confirmation and payment processing
- Receipt generation with PDF export capability
- Automatic table status updates (Available/Occupied)

### Inventory Management
- Item categorization and barcode support
- Real-time stock tracking with automatic deduction
- Low stock alerts and inventory logging
- Cost tracking and profit margin calculations

### Customer Loyalty System
- Points-based rewards program
- Membership levels (Silver, Gold, VIP)
- Customer address management for deliveries
- Purchase history tracking

### Multi-language Support
- English and Arabic language support
- RTL (Right-to-Left) layout for Arabic
- Translation system with centralized dictionary
- Language switching capability

## Data Flow

### Order Processing Flow
1. User selects order type and customer/table information
2. Items are added to cart with real-time total calculation
3. Discounts and tax are applied automatically
4. Order is saved to database with inventory deduction
5. Payment processing creates billing record
6. Receipt is generated and can be printed/exported

### Inventory Management Flow
1. Items are added with initial stock quantities
2. Stock is automatically deducted when orders are placed
3. Low stock alerts are triggered when thresholds are reached
4. Inventory logs track all stock movements
5. Reports show inventory status and movement history

### User Authentication Flow
1. Users enter username/password on login page
2. Credentials are validated against database
3. User sessions are managed with Flask-Login
4. Role-based permissions are enforced on routes using @login_required decorator
5. Session management maintains user state
6. Logout clears session and redirects to login page

### Enhanced Table Management Flow
1. Users click on table in table plan to open split-screen ordering interface
2. Left side shows selected items with real-time total calculation
3. Right side shows categorized menu with search functionality
4. Click menu items to add to cart, adjust quantities as needed
5. Confirm button creates order and marks table as occupied
6. Pay button processes payment and frees up table
7. Order status automatically updates throughout the process

### Professional POS Sales Flow (IRS-Style)
1. Access professional sales screen via "POS Terminal" navigation
2. Search products by name or barcode using left panel
3. Filter by category or use quick access buttons for popular items
4. Add items to cart with automatic price calculation and stock validation
5. Select customer and order type (dine-in, takeaway, delivery)
6. Apply discounts and view tax calculations in real-time
7. Process payment with multiple methods (cash with change calculation, card)
8. Generate receipt and update inventory automatically
9. Customer loyalty points and membership levels updated automatically

## External Dependencies

### Python Packages
- Flask: Web framework
- SQLAlchemy: Database ORM
- Flask-Login: User session management
- Werkzeug: Security utilities
- ReportLab: PDF generation for receipts

### Frontend Dependencies
- Bootstrap 5: UI framework
- Font Awesome: Icons
- Custom JavaScript: Cart and POS functionality

### Database
- PostgreSQL: Primary database (configurable)
- Connection pooling with automatic reconnection
- Environment-based configuration

## Deployment Strategy

### Environment Configuration
- Database URL via DATABASE_URL environment variable
- Session secret via SESSION_SECRET environment variable
- Debug mode configurable for development vs production

### File Structure
```
/
├── app.py              # Main Flask application
├── main.py             # Application entry point
├── models.py           # Database models
├── translations.py     # Multi-language support
├── routes/             # Blueprint modules
│   ├── auth.py         # User authentication
│   ├── orders.py       # Order management
│   ├── customers.py    # Customer management
│   ├── inventory.py    # Inventory management
│   ├── reports.py      # Reporting system
│   ├── settings.py     # System settings
│   └── tables.py       # Enhanced table management
├── templates/          # Jinja2 templates
├── static/             # CSS, JS, images
├── utils/              # Helper functions
│   ├── helpers.py      # Common utilities
│   └── pdf_generator.py # Receipt generation
```

### Security Considerations
- Password hashing with Werkzeug
- CSRF protection through Flask-WTF
- Role-based access control
- SQL injection protection through SQLAlchemy ORM
- Secure session management

### Performance Optimizations
- Database connection pooling
- Lazy loading for relationships
- Efficient query patterns
- Static file optimization
- Responsive design for mobile devices

The system is designed to be scalable and maintainable, with clear separation of concerns between models, views, and business logic. The modular blueprint structure allows for easy extension and modification of functionality.

## Recent Changes: Latest modifications with dates

### 2025-07-14: Professional POS System Implementation
- **Complete IRS POS System Replication**: Built professional three-panel sales interface
- **Advanced Product Search**: Real-time search with barcode support and category filtering
- **Professional Cart Management**: Real-time calculations with tax, discount, and payment processing
- **Customer Loyalty System**: Automatic points calculation and membership level upgrades
- **Payment Processing**: Multiple payment methods with change calculation for cash payments
- **Database Schema Fixed**: Added missing status column and proper order tracking
- **API Endpoints**: Complete REST API for search, customer management, and sales processing
- **Professional UI**: Bootstrap-based interface matching IRS POS system design principles