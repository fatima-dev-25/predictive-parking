// frontend/src/api.js
import axios from 'axios';
const BASE = process.env.REACT_APP_API_BASE || 'http://127.0.0.1:5000';
export const api = axios.create({ baseURL: BASE + '/api' });
