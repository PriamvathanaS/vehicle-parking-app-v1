from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from controller.database import db
from controller.model import Admin, User, ParkingLot, ParkingSpot, ReserveParkingSpot

# Create Blueprint
bp = Blueprint('main', __name__)

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
                session['user_type'] = 'admin'
                session['user_id'] = admin.id
                session['user_email'] = admin.email
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
                session['user_type'] = 'user'
                session['user_id'] = user.id
                session['user_email'] = user.email
                session['user_name'] = user.full_name
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
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash('Email already registered! Please login instead.', 'error')
        return redirect(url_for('main.home'))
    
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
    
    flash('Registration successful! Please login with your credentials.', 'success')
    return redirect(url_for('main.home'))

@bp.route('/logout')
def logout():
    """Handle logout"""
    session.clear()
    flash('You have been logged out successfully!', 'info')
    return redirect(url_for('main.home'))

@bp.route('/admin-dashboard')
def admin_dashboard():
    """Admin dashboard page"""
    # Check if user is logged in as admin
    if session.get('user_type') != 'admin':
        flash('Please login as admin to access this page.', 'error')
        return redirect(url_for('main.home'))
    
    print("Admin dashboard accessed successfully")  # Debug log
    return render_template('admin-dashboard.html')

@bp.route('/user-dashboard')
def user_dashboard():
    """User dashboard page"""
    # Check if user is logged in as user
    if session.get('user_type') != 'user':
        flash('Please login as user to access this page.', 'error')
        return redirect(url_for('main.home'))
    
    # Get user information from session
    user_name = session.get('user_name', 'User')
    user_email = session.get('user_email', '')
    
    return render_template('user-dashboard.html', user_name=user_name, user_email=user_email)

@bp.route('/admin/users')
def admin_users():
    """Admin users management page"""
    # Check if user is logged in as admin
    if session.get('user_type') != 'admin':
        flash('Please login as admin to access this page.', 'error')
        return redirect(url_for('main.home'))
    
    return render_template('admin-user.html')

@bp.route('/admin/home')
def admin_home():
    """Admin parking management page"""
    # Check if user is logged in as admin
    if session.get('user_type') != 'admin':
        flash('Please login as admin to access this page.', 'error')
        return redirect(url_for('main.home'))
    
    return render_template('admin-home.html')

@bp.route('/api/lots', methods=['GET'])
def get_lots():
    """Get all parking lots with their spots"""
    print("🔧 DEBUG: GET /api/lots - Fetching all parking lots")
    
    try:
        lots = ParkingLot.query.all()
        print(f"🔧 DEBUG: Found {len(lots)} parking lots in database")
        
        result = []
        for lot in lots:
            occupied_count = sum(1 for s in lot.spots if s.status == 'O')
            print(f"🔧 DEBUG: Lot {lot.id} has {occupied_count}/{len(lot.spots)} occupied spots")
            
            result.append({
                "id": lot.id,
                "name": lot.prime_location_name,
                "address": lot.address,
                "pinCode": lot.pin_code,
                "pricePerHour": lot.price,
                "totalSpots": lot.maximum_number_of_spots,
                "occupiedSpots": occupied_count,
                "spots": [
                    {
                        "id": s.id,
                        "occupied": s.status == 'O',
                        "customer": None  # No customer data
                    } for s in lot.spots
                ]
            })
        
        print(f"🔧 DEBUG: Returning {len(result)} lots to frontend")
        return jsonify(result)
        
    except Exception as e:
        print(f"🔧 DEBUG: ERROR in get_lots: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/lots', methods=['POST'])
def add_lot():
    """Add new parking lot - SIMPLIFIED VERSION"""
    print("🔧 DEBUG: POST /api/lots - Adding new parking lot")
    
    try:
        # Check admin access
        if session.get('user_type') != 'admin':
            print("🔧 DEBUG: Access denied - not admin user")
            return jsonify({"error": "Admin access required"}), 403
        
        # Get JSON data
        if not request.is_json:
            print(f"🔧 DEBUG: ERROR: Request is not JSON. Content-Type: {request.content_type}")
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        print(f"🔧 DEBUG: Received data: {data}")
        
        if data is None:
            print("🔧 DEBUG: ERROR: No JSON data received")
            return jsonify({"error": "No JSON data received"}), 400
        
        # Extract and validate data
        name = str(data.get('name', '')).strip()
        address = str(data.get('address', '')).strip()
        pin_code = str(data.get('pinCode', '')).strip()
        price_per_hour = float(data.get('pricePerHour', 0))
        total_spots = int(data.get('totalSpots', 0))
        
        print(f"🔧 DEBUG: Parsed data - name='{name}', address='{address}', pin_code='{pin_code}', price={price_per_hour}, spots={total_spots}")
        
        # Basic validation
        if not name or not address or not pin_code:
            return jsonify({"error": "Name, address, and pin code are required"}), 400
        
        if price_per_hour <= 0:
            return jsonify({"error": "Price per hour must be greater than 0"}), 400
        
        if total_spots < 5 or total_spots > 50:
            return jsonify({"error": "Total spots must be between 5 and 50"}), 400
        
        # Check for duplicate lot names
        existing_lot = ParkingLot.query.filter_by(prime_location_name=name).first()
        if existing_lot:
            print(f"🔧 DEBUG: ERROR: Lot with name '{name}' already exists")
            return jsonify({"error": f"Parking lot with name '{name}' already exists"}), 400
        
        # Create new parking lot
        lot = ParkingLot(
            prime_location_name=name,
            address=address,
            pin_code=pin_code,
            price=price_per_hour,
            maximum_number_of_spots=total_spots
        )
        
        print(f"🔧 DEBUG: Created lot object")
        
        # Add to session and flush to get ID
        db.session.add(lot)
        db.session.flush()
        
        lot_id = lot.id
        print(f"🔧 DEBUG: Lot added to session with ID: {lot_id}")
        
        # Create simple parking spots (NO CUSTOMER DATA)
        spots_created = 0
        for i in range(total_spots):
            spot = ParkingSpot(
                lot_id=lot_id, 
                status='A'  # Just available status, no customer data
            )
            db.session.add(spot)
            spots_created += 1
        
        print(f"🔧 DEBUG: Created {spots_created} simple parking spots")
        
        # Commit all changes
        db.session.commit()
        print("🔧 DEBUG: Database commit successful")
        
        success_message = f"Parking lot '{name}' created successfully with {total_spots} spots"
        print(f"🔧 DEBUG: SUCCESS: {success_message}")
        
        return jsonify({
            "success": True,
            "message": success_message,
            "lot_id": lot_id
        }), 201
        
    except Exception as e:
        print(f"🔧 DEBUG: ERROR in add_lot: {str(e)}")
        import traceback
        print(f"🔧 DEBUG: Traceback: {traceback.format_exc()}")
        
        try:
            db.session.rollback()
            print("🔧 DEBUG: Database rollback completed")
        except Exception as rollback_error:
            print(f"🔧 DEBUG: Rollback error: {str(rollback_error)}")
        
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@bp.route('/api/lots/<int:lot_id>/spots/<int:spot_id>/toggle', methods=['POST'])
def toggle_spot(lot_id, spot_id):
    """Toggle parking spot occupancy status - SIMPLIFIED VERSION"""
    print(f"🔧 DEBUG: POST toggle spot - lot_id: {lot_id}, spot_id: {spot_id}")
    
    try:
        # Validate admin access
        if session.get('user_type') != 'admin':
            print("🔧 DEBUG: Access denied - not admin user")
            return jsonify({"error": "Admin access required"}), 403
        
        spot = ParkingSpot.query.filter_by(lot_id=lot_id, id=spot_id).first()
        
        if not spot:
            print(f"🔧 DEBUG: ERROR: Spot not found - lot_id: {lot_id}, spot_id: {spot_id}")
            return jsonify({"error": "Parking spot not found"}), 404
        
        print(f"🔧 DEBUG: Found spot - current status: {spot.status}")
        
        # Simple toggle - just change status, no customer data
        if spot.status == 'A':
            spot.status = 'O'  # Mark as occupied
            print(f"🔧 DEBUG: Marked spot as occupied")
        else:
            spot.status = 'A'  # Mark as available
            print(f"🔧 DEBUG: Marked spot as available")
        
        db.session.commit()
        print("🔧 DEBUG: Spot status updated successfully")
        
        return jsonify({
            "success": True,
            "message": f"Spot status updated to {'occupied' if spot.status == 'O' else 'available'}",
            "new_status": spot.status
        })
        
    except Exception as e:
        print(f"🔧 DEBUG: ERROR in toggle_spot: {str(e)}")
        try:
            db.session.rollback()
        except:
            pass
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
        
        # Delete the lot
        db.session.delete(lot)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Parking lot deleted successfully"})
        
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