from flask import Blueprint, request, jsonify
from controller.model import db, ParkingLot, ParkingSpot

api = Blueprint('api', __name__)

# Get all parking lots
@api.route('/api/lots', methods=['GET'])
def get_lots():
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

# Add new parking lot
@api.route('/api/lots', methods=['POST'])
def add_lot():
    data = request.json
    lot = ParkingLot(
        prime_location_name=data['name'],
        address=data['address'],
        pin_code=data['pinCode'],
        price=data['pricePerHour'],
        maximum_number_of_spots=data['totalSpots']
    )
    db.session.add(lot)
    db.session.commit()
    # Create spots
    for i in range(1, lot.maximum_number_of_spots + 1):
        spot = ParkingSpot(lot_id=lot.id, status='A')
        db.session.add(spot)
    db.session.commit()
    return jsonify({"success": True}), 201

# Edit parking lot
@api.route('/api/lots/<int:lot_id>', methods=['PUT'])
def edit_lot(lot_id):
    data = request.json
    lot = ParkingLot.query.get_or_404(lot_id)
    lot.prime_location_name = data['name']
    lot.address = data['address']
    lot.pin_code = data['pinCode']
    lot.price = data['pricePerHour']
    db.session.commit()
    return jsonify({"success": True})

# Delete parking lot
@api.route('/api/lots/<int:lot_id>', methods=['DELETE'])
def delete_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    ParkingSpot.query.filter_by(lot_id=lot.id).delete()
    db.session.delete(lot)
    db.session.commit()
    return jsonify({"success": True})

# Toggle spot occupancy
@api.route('/api/lots/<int:lot_id>/spots/<int:spot_id>/toggle', methods=['POST'])
def toggle_spot(lot_id, spot_id):
    spot = ParkingSpot.query.filter_by(lot_id=lot_id, id=spot_id).first_or_404()
    if spot.status == 'A':
        spot.status = 'O'
        spot.customer_id = "CUST" + str(spot.id)
        spot.vehicle_number = "MH12AB" + str(1000 + spot.id)
        spot.entry_date = "2024-07-22"
    else:
        spot.status = 'A'
        spot.customer_id = None
        spot.vehicle_number = None
        spot.entry_date = None
    db.session.commit()
    return jsonify({"success": True})

# Clear all parking lots
@api.route('/api/lots', methods=['DELETE'])
def clear_lots():
    ParkingSpot.query.delete()
    ParkingLot.query.delete()
    db.session.commit()
    return jsonify({"success": True})