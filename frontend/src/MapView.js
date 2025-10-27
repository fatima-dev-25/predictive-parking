import React, {useEffect, useState, useRef} from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { api } from './api';
import io from 'socket.io-client';
import LotCard from './LotCard';
const SOCKET_URL = process.env.REACT_APP_API_BASE || 'http://127.0.0.1:5000';

export default function MapView(){
  const [lots, setLots] = useState([]);
  const socketRef = useRef();

  useEffect(()=>{
    api.get('/parking_lots').then(res => setLots(res.data));
    // connect socket
    socketRef.current = io(SOCKET_URL);
    socketRef.current.on('occupancy_update', (data) => {
      // update lot in state
      setLots(prev => prev.map(l => l.id === data.parking_lot_id ? {...l, free: data.free, occupied: data.occupied} : l));
    });
    return () => socketRef.current.disconnect();
  }, []);

  return (
    <div style={{display:'flex', height:'90%'}}>
      <div style={{flex:1}}>
        <MapContainer center={[12.9716,77.5946]} zoom={13} style={{height:'100%'}}>
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {lots.map(l => (
            <Marker key={l.id} position={[l.latitude, l.longitude]}>
              <Popup>
                <strong>{l.name}</strong><br/>
                Free: {l.free} / {l.total_slots}
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
      <div style={{width: '360px', padding: '10px', overflowY: 'auto', borderLeft: '1px solid #eee'}}>
        {lots.map(l => <LotCard key={l.id} lot={l} />)}
      </div>
    </div>
  );
}
