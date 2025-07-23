from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from controller.database import db
from controller.model import Admin, User, ParkingLot, ParkingSpot, ReserveParkingSpot

# Create Blueprint
bp = Blueprint('main', __name__)

# ================================
# AUTHENTICATION ROUTES
# ================================

@bp.route('/')
def home():
    """Home page - Login form"""
    return render_template('login.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user and admin login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        print(f"Login attempt - Email: {email}")  # Debug log
        
        # Validate input
        if not email or not password:
            flash('Please enter both email and password!', 'error')
            return render_template('login.html')
        
        # Check if it's admin login FIRST
        admin = Admin.query.filter_by(email=email).first()
        if admin:
            print(f"Found admin account for: {email}")  # Debug log
            if admin.check_password(password):
                print("Admin password correct - redirecting to admin dashboard")  # Debug log
                flash('Welcome Admin! Login successful!', 'success')
                return redirect(url_for('main.admin_dashboard'))
            else:
                print("Admin password incorrect")  # Debug log
        
        # Check if it's user login
        user = User.query.filter_by(email=email, is_active=True).first()
        if user:
            print(f"Found user account for: {email}")  # Debug log
            if user.check_password(password):
                print("User password correct - redirecting to user dashboard")  # Debug log
                flash('Welcome! Login successful!', 'success')
                return redirect(url_for('main.user_dashboard'))
            else:
                print("User password incorrect")  # Debug log
        
        print("No matching account found or password incorrect")  # Debug log
        flash('Invalid email or password! Please try again.', 'error')
    
    return render_template('login.html')

@bp.route('/register', methods=['POST'])
def register():
    """Handle user registration - Save to database"""
    
    # Get form data
    email = request.form['email']
    password = request.form['password']
    full_name = request.form['fullname']
    address = request.form['address']
    pincode = request.form['pincode']
    
    # Create new user
    new_user = User(
        email=email,
        full_name=full_name,
        address=address,
        pin_code=pincode
    )
    new_user.set_password(password)
    
    # Save to database
    db.session.add(new_user)
    db.session.commit()
    
    flash('Registration successful!', 'success')
    return redirect(url_for('main.home'))
@bp.route('/logout')
def logout():
    """Handle logout"""
    flash('You have been logged out successfully!', 'info')
    return redirect(url_for('main.home'))

# ================================
# DASHBOARD ROUTES
# ================================

@bp.route('/admin-dashboard')
def admin_dashboard():
    """Admin dashboard page"""
    print("Admin dashboard accessed successfully")  # Debug log
    return render_template('admin-dashboard.html')

@bp.route('/test-admin')
def test_admin():
    """Test route to verify admin account exists"""
    admin = Admin.query.filter_by(email='admin@gmail.com').first()
    if admin:
        return f"""
        <h2>✅ Admin Account Exists!</h2>
        <p><strong>Email:</strong> {admin.email}</p>
        <p><strong>Created:</strong> {admin.created_at}</p>
        <p><strong>Password Test:</strong> {'✅ Correct' if admin.check_password('Admin@123') else '❌ Incorrect'}</p>
        <hr>
        <h3>Login Test:</h3>
        <form method="POST" action="/login">
            <p>Email: <input type="email" name="email" value="admin@gmail.com" readonly></p>
            <p>Password: <input type="password" name="password" value="Admin@123"></p>
            <p><button type="submit">Test Admin Login</button></p>
        </form>
        <p><a href="/">← Back to Login Page</a></p>
        """
    else:
        return """
        <h2>❌ Admin Account Not Found!</h2>
        <p>Admin account was not created properly.</p>
        <p><a href="/">← Back to Login Page</a></p>
        """

@bp.route('/user-dashboard')
def user_dashboard():
    """User dashboard page"""
    # You can create a user dashboard template later
    return """
    <h1>User Dashboard - Coming Soon!</h1>
    <p>This page will contain user-specific parking features.</p>
    <a href="/" style="color: blue;">← Back to Login</a>
    """

# ================================
# API ROUTES FOR PARKING MANAGEMENT
# ================================

@bp.route('/api/lots', methods=['GET'])
def get_lots():
    """Get all parking lots with their spots"""
    try:
        lots = ParkingLot.query.all()
        result = []
        
        for lot in lots:
            result.append({
                "id": lot.id,
                "name": lot.prime_location_name,
                "address": lot.address,
                "pinCode": lot.pin_code,
                "pricePerHour": lot.price,
                "totalSpots": lot.maximum_number_of_spots,
                "occupiedSpots": sum(1 for s in lot.spots if s.status == 'O'),
                "spots": [
                    {
                        "id": s.id,
                        "occupied": s.status == 'O',
                        "customer": s.customer_info()
                    } for s in lot.spots
                ]
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/api/lots', methods=['POST'])
def add_lot():
    """Add new parking lot"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['name', 'address', 'pinCode', 'pricePerHour', 'totalSpots']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Check if lot name already exists
        existing_lot = ParkingLot.query.filter_by(prime_location_name=data['name']).first()
        if existing_lot:
            return jsonify({"error": "Parking lot with this name already exists"}), 400
        
        # Create new parking lot
        lot = ParkingLot(
            prime_location_name=data['name'],
            address=data['address'],
            pin_code=data['pinCode'],
            price=data['pricePerHour'],
            maximum_number_of_spots=data['totalSpots']
        )
        
        db.session.add(lot)
        db.session.commit()
        
        # Create parking spots for this lot
        for i in range(1, lot.maximum_number_of_spots + 1):
            spot = ParkingSpot(lot_id=lot.id, status='A')
            db.session.add(spot)
        
        db.session.commit()
        
        return jsonify({"success": True, "message": "Parking lot created successfully"}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/api/lots/<int:lot_id>', methods=['PUT'])
def edit_lot(lot_id):
    """Edit existing parking lot"""
    try:
        data = request.json
        lot = ParkingLot.query.get_or_404(lot_id)
        
        # Check if new name conflicts with existing lots (excluding current lot)
        if 'name' in data:
            existing_lot = ParkingLot.query.filter(
                ParkingLot.prime_location_name == data['name'],
                ParkingLot.id != lot_id
            ).first()
            if existing_lot:
                return jsonify({"error": "Parking lot with this name already exists"}), 400
        
        # Update lot details
        if 'name' in data:
            lot.prime_location_name = data['name']
        if 'address' in data:
            lot.address = data['address']
        if 'pinCode' in data:
            lot.pin_code = data['pinCode']
        if 'pricePerHour' in data:
            lot.price = data['pricePerHour']
        
        db.session.commit()
        
        return jsonify({"success": True, "message": "Parking lot updated successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/api/lots/<int:lot_id>', methods=['DELETE'])
def delete_lot(lot_id):
    """Delete parking lot and all its spots"""
    try:
        lot = ParkingLot.query.get_or_404(lot_id)
        
        # Check if any spots are occupied
        occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
        if occupied_spots > 0:
            return jsonify({"error": "Cannot delete lot with occupied spots"}), 400
        
        # Delete all spots first
        ParkingSpot.query.filter_by(lot_id=lot.id).delete()
        
        # Delete reservations for this lot's spots
        spot_ids = [spot.id for spot in lot.spots]
        if spot_ids:
            ReserveParkingSpot.query.filter(ReserveParkingSpot.spot_id.in_(spot_ids)).delete()
        
        # Delete the lot
        db.session.delete(lot)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Parking lot deleted successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/api/lots/<int:lot_id>/spots/<int:spot_id>/toggle', methods=['POST'])
def toggle_spot(lot_id, spot_id):
    """Toggle parking spot occupancy status"""
    try:
        spot = ParkingSpot.query.filter_by(lot_id=lot_id, id=spot_id).first_or_404()
        
        if spot.status == 'A':
            # Mark as occupied
            spot.status = 'O'
            spot.customer_id = "CUST" + str(spot.id)
            spot.vehicle_number = "MH12AB" + str(1000 + spot.id)
            spot.entry_date = "2024-07-22"
        else:
            # Mark as available
            spot.status = 'A'
            spot.customer_id = None
            spot.vehicle_number = None
            spot.entry_date = None
        
        db.session.commit()
        
        return jsonify({"success": True, "message": "Spot status updated successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/api/lots', methods=['DELETE'])
def clear_lots():
    """Clear all parking lots and spots (Admin function)"""
    try:
        # Delete all reservations first
        ReserveParkingSpot.query.delete()
        
        # Delete all spots
        ParkingSpot.query.delete()
        
        # Delete all lots
        ParkingLot.query.delete()
        
        db.session.commit()
        
        return jsonify({"success": True, "message": "All parking data cleared successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ================================
# USER MANAGEMENT ROUTES (Admin Only)
# ================================

@bp.route('/api/users', methods=['GET'])
def get_users():
    """Get all registered users (Admin only)"""
    try:
        users = User.query.all()
        result = []
        
        for user in users:
            result.append({
                "id": user.id,
                "email": user.email,
                "fullName": user.full_name,
                "address": user.address,
                "pinCode": user.pin_code,
                "isActive": user.is_active,
                "createdAt": user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user_status(user_id):
    """Update user status (activate/deactivate)"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.json
        
        if 'isActive' in data:
            user.is_active = data['isActive']
            db.session.commit()
            
            status = "activated" if user.is_active else "deactivated"
            return jsonify({"success": True, "message": f"User {status} successfully"})
        
        return jsonify({"error": "No valid fields to update"}), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete user account (Admin only)"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Delete user's reservations first
        ReserveParkingSpot.query.filter_by(user_id=user.id).delete()
        
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({"success": True, "message": "User deleted successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ================================
# STATISTICS ROUTES (Admin)
# ================================

@bp.route('/api/stats/dashboard', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics for admin"""
    try:
        total_lots = ParkingLot.query.count()
        total_spots = ParkingSpot.query.count()
        occupied_spots = ParkingSpot.query.filter_by(status='O').count()
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        
        stats = {
            "totalLots": total_lots,
            "totalSpots": total_spots,
            "occupiedSpots": occupied_spots,
            "availableSpots": total_spots - occupied_spots,
            "occupancyRate": round((occupied_spots / total_spots * 100), 2) if total_spots > 0 else 0,
            "totalUsers": total_users,
            "activeUsers": active_users,
            "inactiveUsers": total_users - active_users
        }
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@bp.route('/check-users')
def check_users():
    """Simple route to check saved users"""
    users = User.query.all()
    
    html = "<h2>Registered Users:</h2>"
    
    if users:
        for user in users:
            html += f"""
            <p><strong>Email:</strong> {user.email}<br>
            <strong>Name:</strong> {user.full_name}<br>
            <strong>Address:</strong> {user.address}<br>
            <strong>Pin Code:</strong> {user.pin_code}<br><hr></p>
            """
    else:
        html += "<p>No users found.</p>"
    
    html += '<a href="/">Back to Login</a>'
    return html

# ================================
# ERROR HANDLERS
# ================================

@bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Resource not found"}), 404

@bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return jsonify({"error": "Internal server error"}), 500