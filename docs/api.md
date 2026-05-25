import axios from 'axios';

const API_BASE = '/api';

export const fetchData = () => axios.get(`${API_BASE}/data`);
export const updateData = (id, payload) => axios.put(`${API_BASE}/data/${id}`, payload);
export const deleteData = (id) => axios.delete(`${API_BASE}/data/${id}`);
