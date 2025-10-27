# backend/app.py
import os
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
load_dotenv()
from models import db, configure_app, ParkingLot, ParkingSlot, Booking, OccupancyHistory
from datetime import datetime, timedelta
from prediction import predict_future_free

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secret!')
configure_app(app)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

@app.route('/api/parking_lots', methods=['GET'])
def get_parking_lots():
    lots = ParkingLot.query.all()
    out = []
    for l in lots:
        total = l.total_slots
        occupied = ParkingSlot.query.filter_by(parking_lot_id=l.id, is_occupied=True).count()
        free = total - occupied
        out.append({
            'id': l.id, 'name': l.name, 'address': l.address,
            'latitude': l.latitude, 'longitude': l.longitude,
            'total_slots': total, 'occupied': occupied, 'free': free
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
    data = request.json
    user_id = data.get('user_id', 1)  # for demo use default user
    lot_id = data['parking_lot_id']
    start_time = datetime.fromisoformat(data['start_time'])
    end_time = datetime.fromisoformat(data['end_time'])

    # Begin transaction
    with db.engine.begin() as conn:
        # find a free slot and lock it
        res = conn.execute(
            "SELECT id FROM parking_slots WHERE parking_lot_id=%s AND is_occupied=FALSE LIMIT 1 FOR UPDATE",
            (lot_id,)
        ).fetchone()
        if not res:
            return jsonify({'error': 'No free slots'}), 400
        slot_id = res[0]
        # mark occupied
        conn.execute("UPDATE parking_slots SET is_occupied=TRUE WHERE id=%s", (slot_id,))
        # insert booking
        conn.execute(
            "INSERT INTO bookings (user_id, slot_id, parking_lot_id, start_time, end_time, status, payment_status) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (user_id, slot_id, lot_id, start_time, end_time, 'reserved', 'pending')
        )
        # get inserted booking id
        b = conn.execute("SELECT LAST_INSERT_ID()").fetchone()
        booking_id = b[0]

    # push realtime update
    total = ParkingLot.query.get(lot_id).total_slots
    occupied = ParkingSlot.query.filter_by(parking_lot_id=lot_id, is_occupied=True).count()
    free = total - occupied
    socketio.emit('occupancy_update', {'parking_lot_id': lot_id, 'occupied': occupied, 'free': free})
    return jsonify({'booking_id': booking_id, 'slot_id': slot_id, 'status': 'reserved'})

@app.route('/api/bookings/<int:booking_id>/cancel', methods=['POST'])
def cancel_booking(booking_id):
    b = Booking.query.get(booking_id)
    if not b:
        return jsonify({'error': 'Booking not found'}), 404
    # free the slot
    slot = ParkingSlot.query.get(b.slot_id)
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
    data = request.json
    occupied = data.get('occupied')
    total = ParkingLot.query.get(lot_id).total_slots
    # set first N slots to occupied for simplicity
    slots = ParkingSlot.query.filter_by(parking_lot_id=lot_id).order_by(ParkingSlot.id).all()
    for i, s in enumerate(slots):
        s.is_occupied = (i < occupied)
    db.session.commit()
    # write occupancy history
    free = total - occupied
    oh = OccupancyHistory(parking_lot_id=lot_id, timestamp=datetime.utcnow(), occupied_count=occupied, free_count=free)
    db.session.add(oh)
    db.session.commit()
    socketio.emit('occupancy_update', {'parking_lot_id': lot_id, 'occupied': occupied, 'free': free})
    return jsonify({'ok': True})

if __name__ == '__main__':
    # create app context for models if needed
    with app.app_context():
        db.create_all()
    socketio.run(app, host='0.0.0.0', port=5000)
