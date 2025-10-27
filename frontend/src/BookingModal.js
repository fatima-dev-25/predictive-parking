import React, {useState} from 'react';
import { api } from './api';

export default function BookingModal({lot, onClose}) {
  const [duration, setDuration] = useState(60); // minutes
  const [status, setStatus] = useState(null);

  const book = async ()=>{
    const start = new Date().toISOString();
    const end = new Date(Date.now() + duration*60000).toISOString();
    try{
      const res = await api.post('/bookings', { parking_lot_id: lot.id, start_time: start, end_time: end });
      setStatus({ok: true, booking: res.data});
    }catch(e){
      setStatus({ok:false, msg: e.response?.data?.error || 'Booking failed'});
    }
  };

  return (
    <div style={{position:'fixed', right:40, top:80, background:'white', border:'1px solid #ddd', padding:12, zIndex:999}}>
      <h4>Book at {lot.name}</h4>
      <div>Free: {lot.free} / {lot.total_slots}</div>
      <div style={{marginTop:8}}>
        <label>Duration (minutes):</label>
        <input type="number" value={duration} onChange={(e)=>setDuration(parseInt(e.target.value||0))} />
      </div>
      <div style={{marginTop:8}}>
        <button onClick={book}>Reserve</button>
        <button onClick={onClose} style={{marginLeft:8}}>Close</button>
      </div>
      {status && (
        <div style={{marginTop:8}}>
          {status.ok ? <div>Reserved! Booking ID: {status.booking.booking_id}</div> : <div style={{color:'red'}}>{status.msg}</div>}
        </div>
      )}
    </div>
  );
}
