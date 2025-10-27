# backend/prediction.py
from datetime import datetime, timedelta
from models import db, OccupancyHistory
import pandas as pd

def predict_future_free(parking_lot_id, minutes_ahead=60, interval_minutes=5, window=12):
    """
    Returns a list of (timestamp, predicted_free_count) for next minutes_ahead minutes, sampled every interval_minutes.
    Very simple: rolling average of last `window` samples.
    """
    now = datetime.utcnow()
    # fetch recent history for that parking_lot
    rows = OccupancyHistory.query.filter_by(parking_lot_id=parking_lot_id).order_by(OccupancyHistory.timestamp.desc()).limit(window).all()
    if not rows:
        return []
    recent = [r.free_count for r in reversed(rows)]
    avg_free = int(sum(recent) / len(recent))
    preds = []
    steps = minutes_ahead // interval_minutes
    for i in range(1, steps+1):
        ts = now + timedelta(minutes=i*interval_minutes)
        # simple decay/randomness could be added; keep constant for MVP
        preds.append({'timestamp': ts.isoformat(), 'predicted_free': avg_free})
    return preds
