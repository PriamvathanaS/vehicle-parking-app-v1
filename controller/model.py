from controller.database import db

class ParkingLot(db.Model):
    __tablename__ = 'parking_lot'
    
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    address = db.Column(db.Text, nullable=False)
    pin_code = db.Column(db.String(10), nullable=False)
    maximum_number_of_spots = db.Column(db.Integer, nullable=False)

    # Relationship to spots
    spots = db.relationship('ParkingSpot', backref='lot', lazy=True)

class ParkingSpot(db.Model):
    __tablename__ = 'parking_spot'
    
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    status = db.Column(db.String(1), nullable=False, default='A')  # O-occupied, A-available

    # Customer info fields
    customer_id = db.Column(db.String(20), nullable=True)
    vehicle_number = db.Column(db.String(20), nullable=True)
    entry_date = db.Column(db.String(30), nullable=True)

    def occupied(self):
        return self.status == 'O'

    def customer_info(self):
        if self.occupied():
            return {
                "id": self.customer_id,
                "vehicleNumber": self.vehicle_number,
                "entryDate": self.entry_date
            }
        return None

class ReserveParkingSpot(db.Model):
    __tablename__ = 'reserve_parking_spot'
    
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    parking_timestamp = db.Column(db.DateTime, nullable=False)
    leaving_timestamp = db.Column(db.DateTime, nullable=True)
    parking_cost_per_unit_time = db.Column(db.Float, nullable=False)