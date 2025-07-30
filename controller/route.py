from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from controller.database import db
from controller.model import Admin, User, ParkingLot, ParkingSpot, ReserveParkingSpot
from datetime import datetime

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

@bp.route('/change-password', methods=['POST'])
def change_password():
    """Handle password change for admin and users"""
    try:
        # Check if user is logged in
        if 'user_type' not in session or 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Please login first.'}), 401
        
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        # Validate input
        if not current_password or not new_password:
            return jsonify({'success': False, 'message': 'Current password and new password are required.'}), 400
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'New password must be at least 6 characters long.'}), 400
        
        user_type = session['user_type']
        user_id = session['user_id']
        
        # Check if it's admin or user and verify current password
        if user_type == 'admin':
            admin = Admin.query.get(user_id)
            if not admin:
                return jsonify({'success': False, 'message': 'Admin not found.'}), 404
            
            if not admin.check_password(current_password):
                return jsonify({'success': False, 'message': 'Current password is incorrect.'}), 400
            
            # Update password
            admin.set_password(new_password)
            db.session.commit()
            
        elif user_type == 'user':
            user = User.query.get(user_id)
            if not user:
                return jsonify({'success': False, 'message': 'User not found.'}), 404
            
            if not user.check_password(current_password):
                return jsonify({'success': False, 'message': 'Current password is incorrect.'}), 400
            
            # Update password
            user.set_password(new_password)
            db.session.commit()
        
        else:
            return jsonify({'success': False, 'message': 'Invalid user type.'}), 400
        
        return jsonify({'success': True, 'message': 'Password changed successfully!'})
        
    except Exception as e:
        print(f"Error changing password: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while changing password.'}), 500

@bp.route('/get-user-info', methods=['GET'])
def get_user_info():
    """Get current user information"""
    try:
        # Check if user is logged in
        if 'user_type' not in session or 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Please login first.'}), 401
        
        user_type = session['user_type']
        user_id = session['user_id']
        
        if user_type == 'admin':
            admin = Admin.query.get(user_id)
            if not admin:
                return jsonify({'success': False, 'message': 'Admin not found.'}), 404
            
            return jsonify({
                'success': True,
                'user_type': 'admin',
                'username': admin.email.split('@')[0].title(),  # Use part before @ as username
                'email': admin.email,
                'full_name': 'Administrator'
            })
            
        elif user_type == 'user':
            user = User.query.get(user_id)
            if not user:
                return jsonify({'success': False, 'message': 'User not found.'}), 404
            
            return jsonify({
                'success': True,
                'user_type': 'user',
                'username': user.full_name or user.email.split('@')[0].title(),
                'email': user.email,
                'full_name': user.full_name
            })
        
        else:
            return jsonify({'success': False, 'message': 'Invalid user type.'}), 400
            
    except Exception as e:
        print(f"Error getting user info: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while getting user info.'}), 500

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
@bp.route('/admin/search')
def admin_search():
    """Admin search page"""
    # Check if user is logged in as admin
    if session.get('user_type') != 'admin':
        flash('Please login as admin to access this page.', 'error')
        return redirect(url_for('main.home'))
    
    return render_template('admin-search.html')

#route for summary page 
@bp.route('/admin/summary')
def admin_summary():
    """Admin summary/analytics page"""
    # Check if user is logged in as admin
    if session.get('user_type') != 'admin':
        flash('Please login as admin to access this page.', 'error')
        return redirect(url_for('main.home'))
    
    return render_template('admin-summary.html')

# Optional: Add a profile route if you want the "Edit Profile" button to work
@bp.route('/admin/profile')
def admin_profile():
    """Admin profile page"""
    # Check if user is logged in as admin
    if session.get('user_type') != 'admin':
        flash('Please login as admin to access this page.', 'error')
        return redirect(url_for('main.home'))
    
    # For now, redirect back to summary or create a profile template
    flash('Profile editing feature coming soon!', 'info')
    return redirect(url_for('main.admin_summary'))

@bp.route('/api/lots', methods=['GET'])
def get_lots():
    """Get all parking lots with their spots and user information"""
    print("🔧 DEBUG: GET /api/lots - Fetching all parking lots with user data")
    
    try:
        lots = ParkingLot.query.all()
        print(f"🔧 DEBUG: Found {len(lots)} parking lots in database")
        
        result = []
        for lot in lots:
            occupied_count = sum(1 for s in lot.spots if s.status == 'O')
            print(f"🔧 DEBUG: Lot {lot.id} has {occupied_count}/{len(lot.spots)} occupied spots")
            
            spots_data = []
            for spot in lot.spots:
                spot_info = {
                    "id": spot.id,
                    "occupied": spot.status == 'O',
                    "customer": None
                }
                
                # If spot is occupied, get reservation/user information
                if spot.status == 'O':
                    # Get the active reservation for this spot
                    reservation = ReserveParkingSpot.query.filter_by(
                        spot_id=spot.id
                    ).order_by(ReserveParkingSpot.parking_timestamp.desc()).first()
                    
                    if reservation and reservation.user:
                        # Calculate duration and cost
                        current_time = datetime.utcnow()
                        parking_start = reservation.parking_timestamp
                        expected_end = reservation.leaving_timestamp
                        
                        # Calculate actual duration so far
                        actual_duration_hours = (current_time - parking_start).total_seconds() / 3600
                        expected_duration_hours = (expected_end - parking_start).total_seconds() / 3600
                        actual_cost = actual_duration_hours * reservation.parking_cost_per_unit_time
                        
                        spot_info["customer"] = {
                            "userId": reservation.user.id,
                            "userName": reservation.user.full_name,
                            "userEmail": reservation.user.email,
                            "vehicleNumber": reservation.vehicle_number,
                            "contactNumber": reservation.contact_number,
                            "parkingStartTime": parking_start.strftime('%Y-%m-%d %H:%M:%S'),
                            "expectedEndTime": expected_end.strftime('%Y-%m-%d %H:%M:%S'),
                            "actualDuration": round(actual_duration_hours, 2),
                            "expectedDuration": round(expected_duration_hours, 2),
                            "pricePerHour": reservation.parking_cost_per_unit_time,
                            "actualCost": round(actual_cost, 2),
                            "reservationId": reservation.id
                        }
                
                spots_data.append(spot_info)
            
            result.append({
                "id": lot.id,
                "name": lot.prime_location_name,
                "address": lot.address,
                "pinCode": lot.pin_code,
                "pricePerHour": lot.price,
                "totalSpots": lot.maximum_number_of_spots,
                "occupiedSpots": occupied_count,
                "spots": spots_data
            })
        
        print(f"🔧 DEBUG: Returning {len(result)} lots to frontend with user data")
        return jsonify(result)
        
    except Exception as e:
        print(f"🔧 DEBUG: ERROR in get_lots: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Add this new route to your route.py file

@bp.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    """Get current user's profile information"""
    try:
        # Check if user is logged in
        if session.get('user_type') != 'user':
            return jsonify({"error": "User not logged in"}), 401
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "User session invalid"}), 401
        
        # Fetch user from database
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Return user profile data
        profile_data = {
            "id": user.id,
            "email": user.email,
            "fullName": user.full_name,
            "address": user.address,
            "pinCode": user.pin_code,
            "isActive": user.is_active,
            "createdAt": user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None
        }
        
        print(f"🔧 DEBUG: Returning profile for user {user.email}: {profile_data}")
        return jsonify(profile_data)
        
    except Exception as e:
        print(f"🔧 DEBUG: ERROR in get_user_profile: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/user/profile', methods=['PUT'])
def update_user_profile():
    """Update current user's profile information"""
    try:
        # Check if user is logged in
        if session.get('user_type') != 'user':
            return jsonify({"error": "User not logged in"}), 401
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "User session invalid"}), 401
        
        # Fetch user from database
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get update data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Update allowed fields
        if 'fullName' in data:
            user.full_name = data['fullName'].strip()
        if 'address' in data:
            user.address = data['address'].strip()
        if 'pinCode' in data:
            user.pin_code = data['pinCode'].strip()
        
        # Commit changes
        db.session.commit()
        
        # Update session data
        session['user_name'] = user.full_name
        
        print(f"🔧 DEBUG: Updated profile for user {user.email}")
        
        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "fullName": user.full_name,
                "address": user.address,
                "pinCode": user.pin_code
            }
        })
        
    except Exception as e:
        print(f"🔧 DEBUG: ERROR in update_user_profile: {str(e)}")
        db.session.rollback()
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

@bp.route('/api/lots/<int:lot_id>/spots/<int:spot_id>/info', methods=['GET'])
def get_spot_info(lot_id, spot_id):
    """Get detailed information about a specific parking spot for hover functionality"""
    print(f"🔧 DEBUG: GET spot info - lot_id: {lot_id}, spot_id: {spot_id}")
    
    try:
        # Check admin access for security
        if session.get('user_type') != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        
        # Find the spot
        spot = ParkingSpot.query.filter_by(lot_id=lot_id, id=spot_id).first()
        if not spot:
            return jsonify({"error": "Parking spot not found"}), 404
        
        # Get lot information
        lot = ParkingLot.query.get(lot_id)
        if not lot:
            return jsonify({"error": "Parking lot not found"}), 404
        
        # Base spot information
        spot_info = {
            "spotId": spot.id,
            "lotId": lot_id,
            "lotName": lot.prime_location_name,
            "status": "Available" if spot.status == 'A' else "Occupied",
            "pricePerHour": lot.price
        }
        
        # If spot is occupied, get detailed reservation information
        if spot.status == 'O':
            reservation = ReserveParkingSpot.query.filter_by(
                spot_id=spot.id
            ).order_by(ReserveParkingSpot.parking_timestamp.desc()).first()
            
            if reservation and reservation.user:
                # Calculate timing information
                current_time = datetime.utcnow()
                parking_start = reservation.parking_timestamp
                expected_end = reservation.leaving_timestamp
                
                actual_duration_hours = (current_time - parking_start).total_seconds() / 3600
                expected_duration_hours = (expected_end - parking_start).total_seconds() / 3600
                actual_cost = actual_duration_hours * reservation.parking_cost_per_unit_time
                expected_cost = expected_duration_hours * reservation.parking_cost_per_unit_time
                
                # Check if overdue
                is_overdue = current_time > expected_end
                overdue_hours = max(0, (current_time - expected_end).total_seconds() / 3600)
                
                spot_info.update({
                    "userId": reservation.user.id,
                    "userName": reservation.user.full_name,
                    "userEmail": reservation.user.email,
                    "vehicleNumber": reservation.vehicle_number,
                    "contactNumber": reservation.contact_number,
                    "parkingStartTime": parking_start.strftime('%Y-%m-%d %H:%M:%S'),
                    "expectedEndTime": expected_end.strftime('%Y-%m-%d %H:%M:%S'),
                    "currentTime": current_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "actualDuration": round(actual_duration_hours, 2),
                    "expectedDuration": round(expected_duration_hours, 2),
                    "actualCost": round(actual_cost, 2),
                    "expectedCost": round(expected_cost, 2),
                    "isOverdue": is_overdue,
                    "overdueHours": round(overdue_hours, 2) if is_overdue else 0,
                    "reservationId": reservation.id
                })
        
        print(f"🔧 DEBUG: Returning spot info: {spot_info}")
        return jsonify(spot_info)
        
    except Exception as e:
        print(f"🔧 DEBUG: ERROR in get_spot_info: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/lots/<int:lot_id>/spots/<int:spot_id>/toggle', methods=['POST'])
def toggle_spot(lot_id, spot_id):
    """DISABLED: Toggle parking spot occupancy status - Admin cannot manually toggle spots"""
    print(f"🔧 DEBUG: POST toggle spot - DISABLED for lot_id: {lot_id}, spot_id: {spot_id}")
    
    # Return error - admin should not be able to manually toggle spots
    return jsonify({
        "error": "Manual spot toggling is disabled. Spots are automatically managed through user bookings.",
        "message": "Parking spots can only be occupied/released through user bookings from the user dashboard."
    }), 403

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

@bp.route('/api/lots/<int:lot_id>', methods=['PUT'])
def update_lot(lot_id):
    try:
        data = request.get_json()
        lot = ParkingLot.query.get_or_404(lot_id)
        
        # Update all lot details with proper validation using correct field names
        if 'name' in data:
            lot.prime_location_name = data['name']  # Changed from name to prime_location_name
        if 'address' in data:
            lot.address = data['address']
        if 'pinCode' in data:
            lot.pin_code = data['pinCode']  # Changed from pinCode to pin_code
        if 'pricePerHour' in data:
            lot.price = float(data['pricePerHour'])  # Changed from pricePerHour to price
        if 'totalSpots' in data:
            # Validate if spots can be updated
            current_occupied = sum(1 for spot in lot.spots if spot.status == 'O')
            if int(data['totalSpots']) < current_occupied:
                return jsonify({'error': 'Cannot reduce spots below current occupancy'}), 400
            lot.maximum_number_of_spots = int(data['totalSpots'])  # Changed from totalSpots to maximum_number_of_spots
        
        # Commit changes
        db.session.commit()
        return jsonify({
            'message': 'Parking lot updated successfully',
            'lot': {
                'id': lot.id,
                'name': lot.prime_location_name,
                'address': lot.address,
                'pinCode': lot.pin_code,
                'pricePerHour': lot.price,
                'totalSpots': lot.maximum_number_of_spots
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# ================================
# PARKING BOOKING ROUTES (User)
# ================================

@bp.route('/api/book_parking_spot', methods=['POST'])
def book_parking_spot():
    """Book a parking spot for a user"""
    print("🔧 DEBUG: POST /api/book_parking_spot - Booking parking spot")
    
    try:
        # Check if user is logged in
        if session.get('user_type') != 'user':
            print("🔧 DEBUG: Access denied - not a user")
            return jsonify({"error": "Access denied. Please login as a user."}), 401
        
        user_id = session.get('user_id')
        if not user_id:
            print("🔧 DEBUG: No user_id in session")
            return jsonify({"error": "User session not found."}), 401
        
        # Get JSON data
        if not request.is_json:
            print("🔧 DEBUG: Request is not JSON")
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        print(f"🔧 DEBUG: Received booking data: {data}")
        
        if data is None:
            return jsonify({"error": "No data received"}), 400
        
        # Extract and validate required fields
        lot_id = data.get('lotId')
        spot_id = data.get('spotId')
        vehicle_number = data.get('vehicleNumber', '').strip()
        contact_number = data.get('contactNumber', '').strip()
        parking_timestamp = data.get('parkingTimestamp')
        leaving_timestamp = data.get('leavingTimestamp')
        
        print(f"🔧 DEBUG: Extracted data - lot_id: {lot_id}, spot_id: {spot_id}, vehicle: {vehicle_number}")
        
        # Validation
        if not all([lot_id, spot_id, vehicle_number, contact_number, parking_timestamp, leaving_timestamp]):
            return jsonify({"error": "All fields are required"}), 400
        
        # Validate vehicle number format (basic validation)
        if len(vehicle_number) < 6 or len(vehicle_number) > 15:
            return jsonify({"error": "Invalid vehicle number format"}), 400
        
        # Validate contact number format (basic validation)
        if len(contact_number) < 10 or len(contact_number) > 15:
            return jsonify({"error": "Invalid contact number format"}), 400
        
        # Check if lot exists
        lot = ParkingLot.query.get(lot_id)
        if not lot:
            print(f"🔧 DEBUG: Lot {lot_id} not found")
            return jsonify({"error": "Parking lot not found"}), 404
        
        # Check if spot exists and belongs to the lot
        spot = ParkingSpot.query.filter_by(id=spot_id, lot_id=lot_id).first()
        if not spot:
            print(f"🔧 DEBUG: Spot {spot_id} not found in lot {lot_id}")
            return jsonify({"error": "Parking spot not found"}), 404
        
        # Check if spot is available
        if spot.status == 'O':
            print(f"🔧 DEBUG: Spot {spot_id} is already occupied")
            return jsonify({"error": "Parking spot is already occupied"}), 400
        
        # Check if user exists and is active
        user = User.query.filter_by(id=user_id, is_active=True).first()
        if not user:
            print(f"🔧 DEBUG: User {user_id} not found or inactive")
            return jsonify({"error": "User not found or inactive"}), 404
        
        # Parse timestamps
        try:
            parking_dt = datetime.fromisoformat(parking_timestamp.replace('Z', '+00:00'))
            leaving_dt = datetime.fromisoformat(leaving_timestamp.replace('Z', '+00:00'))
        except ValueError as e:
            print(f"🔧 DEBUG: Invalid timestamp format: {e}")
            return jsonify({"error": "Invalid timestamp format"}), 400
        
        # Validate that leaving time is after parking time
        if leaving_dt <= parking_dt:
            return jsonify({"error": "Leaving time must be after parking time"}), 400
        
        # Check for existing active reservations for this user
        existing_reservation = ReserveParkingSpot.query.filter_by(
            user_id=user_id,
            leaving_timestamp=None
        ).first()
        
        if existing_reservation:
            return jsonify({"error": "You already have an active parking reservation"}), 400
        
        # Start database transaction
        print("🔧 DEBUG: Starting database transaction")
        
        # Update parking spot status from 'A' to 'O'
        spot.status = 'O'
        print(f"🔧 DEBUG: Updated spot {spot_id} status to 'O'")
        
        # Create new reservation record
        reservation = ReserveParkingSpot(
            spot_id=spot_id,
            user_id=user_id,
            vehicle_number=vehicle_number.upper(),  # Store in uppercase
            contact_number=contact_number,
            parking_timestamp=parking_dt,
            leaving_timestamp=leaving_dt,
            parking_cost_per_unit_time=lot.price
        )
        
        db.session.add(reservation)
        print(f"🔧 DEBUG: Created reservation record with ID pending")
        
        # Commit transaction
        db.session.commit()
        print("🔧 DEBUG: Database transaction committed successfully")
        
        # Calculate duration and total cost
        duration_hours = (leaving_dt - parking_dt).total_seconds() / 3600
        total_cost = duration_hours * lot.price
        
        success_message = f"Parking spot booked successfully!"
        print(f"🔧 DEBUG: SUCCESS: {success_message}")
        
        # Return success response with booking details
        return jsonify({
            "success": True,
            "message": success_message,
            "booking": {
                "id": reservation.id,
                "lotId": lot_id,
                "lotName": lot.prime_location_name,
                "spotId": spot_id,
                "vehicleNumber": vehicle_number.upper(),
                "contactNumber": contact_number,
                "parkingTimestamp": parking_dt.isoformat(),
                "leavingTimestamp": leaving_dt.isoformat(),
                "duration": round(duration_hours, 2),
                "pricePerHour": lot.price,
                "totalCost": round(total_cost, 2),
                "userName": user.full_name,
                "userEmail": user.email
            }
        }), 201
        
    except Exception as e:
        print(f"🔧 DEBUG: ERROR in book_parking_spot: {str(e)}")
        try:
            db.session.rollback()
            print("🔧 DEBUG: Database rollback completed")
        except Exception as rollback_error:
            print(f"🔧 DEBUG: Rollback error: {str(rollback_error)}")
        
        return jsonify({"error": f"Booking failed: {str(e)}"}), 500

# ================================
# PARKING RELEASE ROUTES (User)
# ================================

@bp.route('/api/release_parking_spot', methods=['POST'])
def release_parking_spot():
    """Release a parking spot when user is done parking"""
    print("🔧 DEBUG: POST /api/release_parking_spot - Releasing parking spot")
    
    try:
        # Check if user is logged in
        if session.get('user_type') != 'user':
            return jsonify({"error": "Access denied. Please login as a user."}), 401
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "User session not found."}), 401
        
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400
        
        reservation_id = data.get('reservationId')
        if not reservation_id:
            return jsonify({"error": "Reservation ID is required"}), 400
        
        # Find the reservation
        reservation = ReserveParkingSpot.query.filter_by(
            id=reservation_id,
            user_id=user_id
        ).first()
        
        if not reservation:
            return jsonify({"error": "Reservation not found or access denied"}), 404
        
        # Get the associated spot
        spot = ParkingSpot.query.get(reservation.spot_id)
        if not spot:
            return jsonify({"error": "Associated parking spot not found"}), 404
        
        # Calculate final costs
        current_time = datetime.utcnow()
        parking_start = reservation.parking_timestamp
        expected_end = reservation.leaving_timestamp
        
        actual_duration_hours = (current_time - parking_start).total_seconds() / 3600
        expected_duration_hours = (expected_end - parking_start).total_seconds() / 3600
        
        final_cost = max(
            actual_duration_hours * reservation.parking_cost_per_unit_time,
            expected_duration_hours * reservation.parking_cost_per_unit_time
        )
        
        # Update reservation with actual leaving time
        reservation.leaving_timestamp = current_time
        
        # Free up the parking spot
        spot.status = 'A'
        
        # Commit changes
        db.session.commit()
        
        is_overdue = current_time > expected_end
        overdue_hours = max(0, (current_time - expected_end).total_seconds() / 3600)
        
        print(f"🔧 DEBUG: Released spot {spot.id} for user {user_id}")
        
        return jsonify({
            "success": True,
            "message": "Parking spot released successfully",
            "releaseDetails": {
                "reservationId": reservation.id,
                "spotId": spot.id,
                "actualEndTime": current_time.strftime('%Y-%m-%d %H:%M:%S'),
                "actualDuration": round(actual_duration_hours, 2),
                "expectedDuration": round(expected_duration_hours, 2),
                "finalCost": round(final_cost, 2),
                "isOverdue": is_overdue,
                "overdueHours": round(overdue_hours, 2) if is_overdue else 0
            }
        })
        
    except Exception as e:
        print(f"🔧 DEBUG: ERROR in release_parking_spot: {str(e)}")
        db.session.rollback()
        return jsonify({"error": f"Release failed: {str(e)}"}), 500

@bp.route('/api/user/bookings', methods=['GET'])
def get_user_bookings():
    """Get current user's booking history"""
    try:
        # Check if user is logged in
        if session.get('user_type') != 'user':
            return jsonify({"error": "User not logged in"}), 401
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "User session invalid"}), 401
        
        # Get all user's reservations
        reservations = ReserveParkingSpot.query.filter_by(user_id=user_id)\
                                                .order_by(ReserveParkingSpot.parking_timestamp.desc())\
                                                .all()
        
        bookings = []
        for reservation in reservations:
            # Get lot information
            spot = ParkingSpot.query.get(reservation.spot_id)
            lot = ParkingLot.query.get(spot.lot_id) if spot else None
            
            if not lot:
                continue
            
            # Determine status
            current_time = datetime.utcnow()
            expected_end = reservation.leaving_timestamp
            actual_end = reservation.leaving_timestamp
            
            # If leaving_timestamp hasn't been updated from original expected time, it's still active
            is_active = (abs((expected_end - actual_end).total_seconds()) < 60) and (current_time < expected_end)
            
            status = "active" if is_active else "completed"
            
            # Calculate costs
            if is_active:
                duration_hours = (current_time - reservation.parking_timestamp).total_seconds() / 3600
            else:
                duration_hours = (actual_end - reservation.parking_timestamp).total_seconds() / 3600
            
            total_cost = duration_hours * reservation.parking_cost_per_unit_time
            
            bookings.append({
                "id": reservation.id,
                "lotId": lot.id,
                "lotName": lot.prime_location_name,
                "spotId": reservation.spot_id,
                "vehicleNumber": reservation.vehicle_number,
                "contactNumber": reservation.contact_number,
                "startTime": reservation.parking_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                "endTime": actual_end.strftime('%Y-%m-%d %H:%M:%S'),
                "duration": round(duration_hours, 2),
                "cost": round(total_cost, 2),
                "status": status,
                "pricePerHour": reservation.parking_cost_per_unit_time
            })
        
        return jsonify(bookings)
        
    except Exception as e:
        print(f"🔧 DEBUG: ERROR in get_user_bookings: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/user/stats', methods=['GET'])
def get_user_stats():
    """Get current user's booking statistics for dashboard"""
    try:
        # Check if user is logged in
        if session.get('user_type') != 'user':
            return jsonify({"error": "User not logged in"}), 401
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "User session invalid"}), 401
        
        # Get all user's reservations
        reservations = ReserveParkingSpot.query.filter_by(user_id=user_id).all()
        
        if not reservations:
            return jsonify({
                "totalBookings": 0,
                "activeBookings": 0,
                "completedBookings": 0,
                "totalSpent": 0,
                "totalHours": 0,
                "avgCostPerHour": 0,
                "locationUsage": [],
                "monthlySpending": [],
                "mostUsedLocation": "N/A",
                "avgDuration": "0h 0m",
                "favoriteTimeSlot": "N/A",
                "lastBooking": "No bookings yet",
                "thisMonthBookings": 0
            })
        
        from collections import defaultdict
        from datetime import datetime, timedelta
        import calendar
        
        current_time = datetime.utcnow()
        current_month = current_time.month
        current_year = current_time.year
        
        # Initialize statistics
        total_bookings = len(reservations)
        active_count = 0
        completed_count = 0
        total_spent = 0
        total_hours = 0
        location_usage = defaultdict(lambda: {"count": 0, "hours": 0, "spent": 0})
        monthly_spending = defaultdict(float)
        time_slot_usage = defaultdict(int)
        this_month_count = 0
        durations = []
        
        for reservation in reservations:
            # Get lot information
            spot = ParkingSpot.query.get(reservation.spot_id)
            lot = ParkingLot.query.get(spot.lot_id) if spot else None
            
            if not lot:
                continue
            
            # Determine status
            expected_end = reservation.leaving_timestamp
            actual_end = reservation.leaving_timestamp
            
            # If leaving_timestamp hasn't been updated from original expected time, it's still active
            is_active = (abs((expected_end - actual_end).total_seconds()) < 60) and (current_time < expected_end)
            
            if is_active:
                active_count += 1
                duration_hours = (current_time - reservation.parking_timestamp).total_seconds() / 3600
            else:
                completed_count += 1
                duration_hours = (actual_end - reservation.parking_timestamp).total_seconds() / 3600
            
            cost = duration_hours * reservation.parking_cost_per_unit_time
            total_spent += cost
            total_hours += duration_hours
            durations.append(duration_hours)
            
            # Location usage
            location_usage[lot.prime_location_name]["count"] += 1
            location_usage[lot.prime_location_name]["hours"] += duration_hours
            location_usage[lot.prime_location_name]["spent"] += cost
            
            # Monthly spending
            booking_month = reservation.parking_timestamp.strftime('%Y-%m')
            monthly_spending[booking_month] += cost
            
            # Time slot analysis (hour of day)
            hour = reservation.parking_timestamp.hour
            if 6 <= hour < 12:
                time_slot_usage["Morning (6-12)"] += 1
            elif 12 <= hour < 18:
                time_slot_usage["Afternoon (12-18)"] += 1
            elif 18 <= hour <= 23:
                time_slot_usage["Evening (18-24)"] += 1
            else:
                time_slot_usage["Night (0-6)"] += 1
            
            # This month bookings
            if (reservation.parking_timestamp.month == current_month and 
                reservation.parking_timestamp.year == current_year):
                this_month_count += 1
        
        # Calculate averages and insights
        avg_cost_per_hour = (total_spent / total_hours) if total_hours > 0 else 0
        
        # Most used location
        most_used_location = max(location_usage.items(), key=lambda x: x[1]["count"])[0] if location_usage else "N/A"
        
        # Average duration
        avg_duration_hours = sum(durations) / len(durations) if durations else 0
        avg_hours = int(avg_duration_hours)
        avg_minutes = int((avg_duration_hours - avg_hours) * 60)
        avg_duration_str = f"{avg_hours}h {avg_minutes}m"
        
        # Favorite time slot
        favorite_time_slot = max(time_slot_usage.items(), key=lambda x: x[1])[0] if time_slot_usage else "N/A"
        
        # Last booking
        latest_reservation = max(reservations, key=lambda x: x.parking_timestamp)
        last_booking_date = latest_reservation.parking_timestamp.strftime('%d %b %Y')
        
        # Prepare location usage for charts
        location_chart_data = [
            {
                "name": location,
                "bookings": data["count"],
                "hours": round(data["hours"], 1),
                "spent": round(data["spent"], 2)
            }
            for location, data in location_usage.items()
        ]
        
        # Prepare monthly spending for charts (last 6 months)
        monthly_chart_data = []
        for i in range(5, -1, -1):
            month_date = current_time.replace(day=1) - timedelta(days=30*i)
            month_key = month_date.strftime('%Y-%m')
            month_name = month_date.strftime('%b %Y')
            spending = monthly_spending.get(month_key, 0)
            monthly_chart_data.append({
                "month": month_name,
                "amount": round(spending, 2)
            })
        
        stats = {
            "totalBookings": total_bookings,
            "activeBookings": active_count,
            "completedBookings": completed_count,
            "totalSpent": round(total_spent, 2),
            "totalHours": round(total_hours, 1),
            "avgCostPerHour": round(avg_cost_per_hour, 2),
            "locationUsage": location_chart_data,
            "monthlySpending": monthly_chart_data,
            "mostUsedLocation": most_used_location,
            "avgDuration": avg_duration_str,
            "favoriteTimeSlot": favorite_time_slot,
            "lastBooking": last_booking_date,
            "thisMonthBookings": this_month_count
        }
        
        return jsonify(stats)
        
    except Exception as e:
        print(f"🔧 DEBUG: ERROR in get_user_stats: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/admin/delete_parking_spot', methods=['DELETE'])
def admin_delete_parking_spot():
    
    
    try:
       
        if session.get('user_type') != 'admin':
            return jsonify({"error": "Access denied. Admin privileges required."}), 401
        
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400
        
        lot_id = data.get('lotId')
        spot_id = data.get('spotId')
        
        if not lot_id or not spot_id:
            return jsonify({"error": "Lot ID and Spot ID are required"}), 400
        
        print(f"🔧 DEBUG: Attempting to delete spot {spot_id} from lot {lot_id}")
        
        # Find the parking spot by ID (since spot ID is unique)
        spot = ParkingSpot.query.get(spot_id)
        if not spot:
            return jsonify({"error": f"Parking spot with ID {spot_id} not found"}), 404
        
        # Verify the spot belongs to the specified lot
        if spot.lot_id != lot_id:
            return jsonify({"error": f"Spot {spot_id} does not belong to lot {lot_id}"}), 400
        
        # Check if spot is occupied
        if spot.status == 'O':
            print(f"🔧 DEBUG: Cannot delete occupied spot {spot_id}")
            return jsonify({"error": "Cannot delete occupied parking spot. Please wait for the spot to be available."}), 400
        
        # Get lot information for response
        lot = ParkingLot.query.get(lot_id)
        if not lot:
            return jsonify({"error": "Parking lot not found"}), 404
        
        # Delete any related reservations (cleanup)
        ReserveParkingSpot.query.filter_by(spot_id=spot.id).delete()
        
        # Delete the parking spot
        db.session.delete(spot)
        
        # Update lot's maximum spots count
        remaining_spots = ParkingSpot.query.filter_by(lot_id=lot_id).count() - 1
        lot.maximum_number_of_spots = remaining_spots
        
        # Commit changes
        db.session.commit()
        
        success_message = f"Parking spot {spot_id} deleted successfully from {lot.prime_location_name}"
        print(f"🔧 DEBUG: SUCCESS: {success_message}")
        
        return jsonify({
            "success": True,
            "message": success_message,
            "deletedSpot": {
                "lotId": lot_id,
                "spotId": spot_id,
                "lotName": lot.prime_location_name,
                "remainingSpots": remaining_spots
            }
        }), 200
        
    except Exception as e:
        print(f"🔧 DEBUG: ERROR in admin_delete_parking_spot: {str(e)}")
        try:
            db.session.rollback()
            print("🔧 DEBUG: Database rollback completed")
        except Exception as rollback_error:
            print(f"🔧 DEBUG: Rollback error: {str(rollback_error)}")
        
        return jsonify({"error": f"Deletion failed: {str(e)}"}), 500

@bp.route('/api/delete_parking_spot', methods=['DELETE'])
def delete_parking_spot():
    """Delete a parking booking and free up the spot"""
    print("🔧 DEBUG: DELETE /api/delete_parking_spot - Deleting parking booking")
    
    try:
        # Check if user is logged in
        if session.get('user_type') != 'user':
            return jsonify({"error": "Access denied. Please login as a user."}), 401
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "User session not found."}), 401
        
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400
        
        reservation_id = data.get('reservationId')
        if not reservation_id:
            return jsonify({"error": "Reservation ID is required"}), 400
        
        print(f"🔧 DEBUG: Attempting to delete reservation {reservation_id} for user {user_id}")
        
        # Find the reservation - must belong to the current user
        reservation = ReserveParkingSpot.query.filter_by(
            id=reservation_id,
            user_id=user_id
        ).first()
        
        if not reservation:
            print(f"🔧 DEBUG: Reservation {reservation_id} not found for user {user_id}")
            return jsonify({"error": "Reservation not found or access denied"}), 404
        
        # Get the associated spot
        spot = ParkingSpot.query.get(reservation.spot_id)
        if not spot:
            print(f"🔧 DEBUG: Associated parking spot {reservation.spot_id} not found")
            return jsonify({"error": "Associated parking spot not found"}), 404
        
        # Get lot information for response
        lot = ParkingLot.query.get(spot.lot_id)
        lot_name = lot.prime_location_name if lot else "Unknown"
        
        # Store details before deletion for response
        spot_id = reservation.spot_id
        vehicle_number = reservation.vehicle_number
        
        print(f"🔧 DEBUG: Found reservation - Spot: {spot_id}, Vehicle: {vehicle_number}, Lot: {lot_name}")
        
        # Start database transaction
        # First, free up the parking spot (change status from 'O' to 'A')
        if spot.status == 'O':
            spot.status = 'A'
            print(f"🔧 DEBUG: Changed spot {spot_id} status from 'O' to 'A'")
        else:
            print(f"🔧 DEBUG: Warning: Spot {spot_id} was not occupied (status: {spot.status})")
        
        # Delete the reservation record
        db.session.delete(reservation)
        print(f"🔧 DEBUG: Marked reservation {reservation_id} for deletion")
        
        # Commit all changes
        db.session.commit()
        print("🔧 DEBUG: Database transaction committed successfully")
        
        success_message = f"Booking deleted successfully! Spot {spot_id} is now available."
        print(f"🔧 DEBUG: SUCCESS: {success_message}")
        
        return jsonify({
            "success": True,
            "message": success_message,
            "deletedBooking": {
                "reservationId": reservation_id,
                "spotId": spot_id,
                "lotName": lot_name,
                "vehicleNumber": vehicle_number,
                "spotStatus": "Available"
            }
        }), 200
        
    except Exception as e:
        print(f"🔧 DEBUG: ERROR in delete_parking_spot: {str(e)}")
        try:
            db.session.rollback()
            print("🔧 DEBUG: Database rollback completed")
        except Exception as rollback_error:
            print(f"🔧 DEBUG: Rollback error: {str(rollback_error)}")
        
        return jsonify({"error": f"Deletion failed: {str(e)}"}), 500