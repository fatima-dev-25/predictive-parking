# backend/app.py
import os
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from dotenv import load_dotenv
load_dotenv()

# app models & helpers
from models import db, configure_app, ParkingLot, ParkingSlot, Booking, OccupancyHistory

# time parsing & sql helpers
from datetime import datetime
from dateutil.parser import isoparse
from sqlalchemy import text

# CORS
from flask_cors import CORS

# Prediction helper
from prediction import predict_future_free

# --- App setup ---
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # allow frontend dev access
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secret!')
configure_app(app)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


# --- Routes ---
@app.route('/api/parking_lots', methods=['GET'])
def get_parking_lots():
    lots = ParkingLot.query.all()
    out = []
    for l in lots:
        total = l.total_slots or 0
        occupied = ParkingSlot.query.filter_by(parking_lot_id=l.id, is_occupied=True).count()
        free = total - occupied
        out.append({
            'id': l.id,
            'name': l.name,
            'address': l.address,
            'latitude': l.latitude,
            'longitude': l.longitude,
            'total_slots': total,
            'occupied': occupied,
            'free': free
        })
    return jsonify(out)


@app.route('/api/parking_lots/<int:lot_id>/prediction', methods=['GET'])
def get_prediction(lot_id):
    preds = predict_future_free(lot_id, minutes_ahead=60, interval_minutes=5, window=12)
    return jsonify(preds)


@app.route('/api/bookings', methods=['POST'])
def create_booking():
    """
    Booking flow:
      1. Receive user_id, parking_lot_id, start_time, end_time
      2. Start DB transaction
      3. SELECT one free slot FOR UPDATE
      4. Mark it occupied and create booking with status reserved
      5. Return booking details
    """
    data = request.json or {}
    # basic validation
    if 'parking_lot_id' not in data or 'start_time' not in data or 'end_time' not in data:
        return jsonify({'error': 'parking_lot_id, start_time and end_time are required'}), 400

    user_id = data.get('user_id', 1)  # demo default user
    lot_id = data['parking_lot_id']

    # parse ISO datetimes from frontend robustly (handles trailing 'Z')
    try:
        start_time = isoparse(data['start_time'])
        end_time = isoparse(data['end_time'])
    except Exception as e:
        return jsonify({'error': f'Invalid datetime format: {e}'}), 400

    # Begin transaction: safely use sqlalchemy.text and bound params
    try:
        with db.engine.begin() as conn:
            # Lock one free slot for update.
            # Note: MySQL supports "FOR UPDATE" here. Optionally use SKIP LOCKED to avoid waiting.
            res = conn.execute(
                text(
                    "SELECT id FROM parking_slots "
                    "WHERE parking_lot_id = :lot_id AND is_occupied = FALSE "
                    "LIMIT 1 FOR UPDATE"
                ),
                {"lot_id": lot_id}
            ).fetchone()

            if not res:
                return jsonify({'error': 'No free slots'}), 400

            slot_id = res[0]

            # Mark the selected slot occupied
            conn.execute(
                text("UPDATE parking_slots SET is_occupied = TRUE WHERE id = :id"),
                {"id": slot_id}
            )

            # Insert booking row
            conn.execute(
                text(
                    "INSERT INTO bookings (user_id, slot_id, parking_lot_id, start_time, end_time, status, payment_status) "
                    "VALUES (:user_id, :slot_id, :lot_id, :start_time, :end_time, :status, :payment_status)"
                ),
                {
                    "user_id": user_id,
                    "slot_id": slot_id,
                    "lot_id": lot_id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "status": "reserved",
                    "payment_status": "pending"
                }
            )

            # Get last insert id from MySQL
            last = conn.execute(text("SELECT LAST_INSERT_ID()")).fetchone()
            booking_id = int(last[0]) if last else None

    except Exception as e:
        # transaction will rollback automatically on exception when using begin()
        return jsonify({'error': f'Database error: {e}'}), 500

    # push realtime update to clients
    total = ParkingLot.query.get(lot_id).total_slots
    occupied = ParkingSlot.query.filter_by(parking_lot_id=lot_id, is_occupied=True).count()
    free = total - occupied
    socketio.emit('occupancy_update', {'parking_lot_id': lot_id, 'occupied': occupied, 'free': free})

    return jsonify({'booking_id': booking_id, 'slot_id': slot_id, 'status': 'reserved'}), 201


@app.route('/api/bookings/<int:booking_id>/cancel', methods=['POST'])
def cancel_booking(booking_id):
    b = Booking.query.get(booking_id)
    if not b:
        return jsonify({'error': 'Booking not found'}), 404

    # free the slot (if exists) and cancel booking
    slot = ParkingSlot.query.get(b.slot_id)
    if slot:
        slot.is_occupied = False
    b.status = 'cancelled'
    db.session.commit()

    # realtime notify
    total = ParkingLot.query.get(b.parking_lot_id).total_slots
    occupied = ParkingSlot.query.filter_by(parking_lot_id=b.parking_lot_id, is_occupied=True).count()
    free = total - occupied
    socketio.emit('occupancy_update', {'parking_lot_id': b.parking_lot_id, 'occupied': occupied, 'free': free})
    return jsonify({'ok': True})


# Admin / simulator endpoint to update occupancy manually (dev only)
@app.route('/api/parking_lots/<int:lot_id>/update-occupancy', methods=['POST'])
def update_occupancy(lot_id):
    data = request.json or {}
    occupied = int(data.get('occupied', 0))
    lot = ParkingLot.query.get(lot_id)
    if not lot:
        return jsonify({'error': 'Parking lot not found'}), 404

    total = lot.total_slots or 0
    # set first N slots to occupied for simplicity
    slots = ParkingSlot.query.filter_by(parking_lot_id=lot_id).order_by(ParkingSlot.id).all()
    for i, s in enumerate(slots):
        s.is_occupied = (i < occupied)
    db.session.commit()

    # write occupancy history
    free = max(0, total - occupied)
    oh = OccupancyHistory(
        parking_lot_id=lot_id,
        timestamp=datetime.utcnow(),
        occupied_count=occupied,
        free_count=free
    )
    db.session.add(oh)
    db.session.commit()

    socketio.emit('occupancy_update', {'parking_lot_id': lot_id, 'occupied': occupied, 'free': free})
    return jsonify({'ok': True})


# --- Start server ---
if __name__ == '__main__':
    # create app context for models if needed
    with app.app_context():
        db.create_all()
    socketio.run(app, host='0.0.0.0', port=5000)
