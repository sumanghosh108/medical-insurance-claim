// API client with axios + mock fallback
import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || '';

const client = axios.create({
    baseURL: BASE_URL,
    timeout: 10000,
    headers: { 'Content-Type': 'application/json' },
});

// Add auth token if present
client.interceptors.request.use((config) => {
    const token = localStorage.getItem('auth_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

export default client;
