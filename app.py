from flask import Flask, jsonify, render_template, request
from controller.database import db
from controller.model import ParkingLot, ParkingSpot  # Adjust model import as needed
import os
 
app = None

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.debug = True
    db_path = os.path.join(app.instance_path, "parking.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    db.init_app(app)
    app.app_context().push()
    return app

app = create_app()

# Create all database tables
db.create_all()

# ROUTES (No Blueprints)
# ========================

@app.route('/')
def dashboard():
    return render_template('dashboard.html')  # Must be in /templates folder

# Get all parking lots
@app.route('/api/lots', methods=['GET'])
def get_lots():
    lots = ParkingLot.query.all()
    result = []
    for lot in lots:
        spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
        result.append({
            "id": lot.id,
            "name": lot.name,
            "address": lot.address,
            "pinCode": lot.pin_code,
            "pricePerHour": lot.price_per_hour,
            "totalSpots": lot.total_spots,
            "occupiedSpots": sum(1 for s in spots if s.occupied),
            "spots": [
                {
                    "id": s.id,
                    "occupied": s.occupied,
                    "customer": s.customer_info() if s.occupied else None
                } for s in spots
            ]
        })
    return jsonify(result)

# Add new parking lot
@app.route('/api/lots', methods=['POST'])
def create_lot():
    data = request.json
    new_lot = ParkingLot(
        name=data['name'],
        address=data['address'],
        pin_code=data['pinCode'],
        price_per_hour=data['pricePerHour'],
        total_spots=data['totalSpots']
    )
    db.session.add(new_lot)
    db.session.commit()
    # Create spots
    for i in range(1, new_lot.total_spots + 1):
        spot = ParkingSpot(lot_id=new_lot.id, spot_number=i, occupied=False)
        db.session.add(spot)
    db.session.commit()
    return jsonify({"success": True}), 201

# Edit parking lot
@app.route('/api/lots/<int:lot_id>', methods=['PUT'])
def edit_lot(lot_id):
    data = request.json
    lot = ParkingLot.query.get_or_404(lot_id)
    lot.name = data['name']
    lot.address = data['address']
    lot.pin_code = data['pinCode']
    lot.price_per_hour = data['pricePerHour']
    db.session.commit()
    return jsonify({"success": True})

# Delete parking lot
@app.route('/api/lots/<int:lot_id>', methods=['DELETE'])
def delete_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    ParkingSpot.query.filter_by(lot_id=lot.id).delete()
    db.session.delete(lot)
    db.session.commit()
    return jsonify({"success": True})

# Toggle spot occupancy
@app.route('/api/lots/<int:lot_id>/spots/<int:spot_id>/toggle', methods=['POST'])
def toggle_spot(lot_id, spot_id):
    spot = ParkingSpot.query.filter_by(lot_id=lot_id, id=spot_id).first_or_404()
    spot.occupied = not spot.occupied
    if spot.occupied:
        # Assign dummy customer info
        spot.customer_id = "CUST" + str(spot.id)
        spot.vehicle_number = "MH12AB" + str(1000 + spot.id)
        spot.entry_date = "2024-07-22"
    else:
        spot.customer_id = None
        spot.vehicle_number = None
        spot.entry_date = None
    db.session.commit()
    return jsonify({"success": True})

# Clear all parking lots
@app.route('/api/lots', methods=['DELETE'])
def clear_lots():
    ParkingSpot.query.delete()
    ParkingLot.query.delete()
    db.session.commit()
    return jsonify({"success": True})

# Example model methods (add to your ParkingSpot model)
# def customer_info(self):
#     return {
#         "id": self.customer_id,
#         "vehicleNumber": self.vehicle_number,
#         "entryDate": self.entry_date
#     }

if __name__ == "__main__":
    app.run(debug=True)
