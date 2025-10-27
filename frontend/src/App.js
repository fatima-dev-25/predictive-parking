import React from 'react';
import MapView from './MapView';
export default function App(){
  return (
    <div style={{height: '100vh'}}>
      <h2 style={{textAlign:'center'}}>Predictive Parking Demo</h2>
      <MapView />
    </div>
  );
}
