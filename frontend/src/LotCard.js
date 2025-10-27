import React, {useState} from 'react';
import BookingModal from './BookingModal';
import { api } from './api';

export default function LotCard({lot}) {
  const [show, setShow] = useState(false);
  const [pred, setPred] = useState([]);

  const loadPred = async () => {
    const res = await api.get(`/parking_lots/${lot.id}/prediction`);
    setPred(res.data);
    setShow(true);
  };

  return (
    <div style={{border:'1px solid #ddd', padding: '10px', marginBottom: '10px', borderRadius:8}}>
      <h4>{lot.name}</h4>
      <div>{lot.address}</div>
      <div style={{marginTop:6}}>Free: <strong>{lot.free}</strong> / {lot.total_slots}</div>
      <div style={{marginTop:8}}>
        <button onClick={loadPred}>View Prediction</button>
        <button style={{marginLeft:8}} onClick={()=>setShow(true)}>Book</button>
      </div>
      {pred.length>0 && (
        <div style={{marginTop:8}}>
          <small>Next predictions:</small>
          <div style={{display:'flex', gap:6, marginTop:4, overflowX:'auto'}}>
            {pred.slice(0,6).map((p,i)=>(
              <div key={i} style={{minWidth:60, padding:6, border:'1px solid #eee', borderRadius:4}}>
                <div style={{fontSize:12}}>{new Date(p.timestamp).getHours() + ':' + new Date(p.timestamp).getMinutes().toString().padStart(2,'0')}</div>
                <div style={{fontWeight:600}}>{p.predicted_free}</div>
              </div>
            ))}
          </div>
        </div>
      )}
      {show && <BookingModal lot={lot} onClose={()=>setShow(false)} />}
    </div>
  );
}
