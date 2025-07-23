from flask import Flask
from controller.database import db
from controller.model import Admin, User, ParkingLot, ParkingSpot, ReserveParkingSpot
import os

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__, instance_relative_config=True)
    app.debug = True
    app.secret_key = 'your-secret-key-change-this-in-production'
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Database configuration
    db_path = os.path.join(app.instance_path, "parking.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    return app

def init_database(app):
    """Initialize database with default admin user"""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Check if admin already exists
            existing_admin = Admin.query.filter_by(email='admin@gmail.com').first()
            
            if not existing_admin:
                # Create default admin user
                admin = Admin(email='admin@gmail.com')
                admin.set_password('Admin@123')
                
                db.session.add(admin)
                db.session.commit()
                print("✅ Default admin user created successfully!")
                print("   📧 Email: admin@gmail.com")
                print("   🔑 Password: Admin@123")
                print("   🌐 Access: http://localhost:5000/")
            else:
                print("✅ Admin user already exists")
                print("   📧 Email: admin@gmail.com")
                print("   🔑 Password: Admin@123")
                
            # Test admin password
            admin = Admin.query.filter_by(email='admin@gmail.com').first()
            if admin and admin.check_password('Admin@123'):
                print("✅ Admin password verification successful")
            else:
                print("❌ Admin password verification failed!")
                
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            db.session.rollback()

# Create the Flask application
app = create_app()

# Initialize database and create default admin
init_database(app)

# Import and register routes from controller
with app.app_context():
    from controller.route import bp
    app.register_blueprint(bp)

if __name__ == "__main__":
    app.run(debug=True)