# backend/models.py
import os
from dotenv import load_dotenv
load_dotenv()
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def configure_app(app):
    user = os.getenv('MYSQL_USER')
    pw = os.getenv('MYSQL_PASSWORD')
    host = os.getenv('MYSQL_HOST', '127.0.0.1')
    port = os.getenv('MYSQL_PORT', '3306')
    db_name = os.getenv('MYSQL_DB', 'parking_db')
    uri = f'mysql+mysqlconnector://{user}:{pw}@{host}:{port}/{db_name}'
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

class ParkingLot(db.Model):
    __tablename__ = 'parking_lots'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    address = db.Column(db.String(255))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    total_slots = db.Column(db.Integer)

class ParkingSlot(db.Model):
    __tablename__ = 'parking_slots'
    id = db.Column(db.Integer, primary_key=True)
    parking_lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id'))
    slot_number = db.Column(db.String(50))
    slot_type = db.Column(db.String(50))
    is_occupied = db.Column(db.Boolean, default=False)

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    slot_id = db.Column(db.Integer, db.ForeignKey('parking_slots.id'))
    parking_lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id'))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(50))
    payment_status = db.Column(db.String(50), default='pending')

class OccupancyHistory(db.Model):
    __tablename__ = 'occupancy_history'
    id = db.Column(db.Integer, primary_key=True)
    parking_lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id'))
    timestamp = db.Column(db.DateTime)
    occupied_count = db.Column(db.Integer)
    free_count = db.Column(db.Integer)
