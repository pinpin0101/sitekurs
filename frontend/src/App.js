import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [roads, setRoads] = useState([]);

  useEffect(() => {
    // Подключение к Django REST API
    axios.get('http://127.0.0.1:8000/api/roads/')
      .then(res => setRoads(res.data))
      .catch(err => console.error(err));
      const simulateSensorChange = (id, currentTemp) => {
    const newTemp = currentTemp + Math.floor(Math.random() * 11) - 5; // Случайная температура +-5 градусов
    
    fetch(`http://127.0.0.1:8000/api/roads/${id}/`, {
        method: 'PATCH', // Метод для частичного обновления данных
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ temp: newTemp }),
    })
    .then(res => res.json())
    .then(() => {
        fetchRoads(); // Перезагрузить данные, чтобы обновить UI
    })
    .catch(err => console.error("Ошибка при обновлении:", err));
};


  }, []);

  return (
    <div style={{ padding: '20px' }}>
      <h1>🛣️ Мониторинг трасс (Django + React)</h1>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {roads.map(road => (
          <div key={road.id} className="card" style={{border: '1px solid #ccc', padding: '10px'}}>
            <h3>{road.name}</h3>
            <p>Статус: {road.status} | Температура: {road.temp}°C</p>
          </div>
        ))}
      </div>
    </div>
  );
}
export default App;