import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';
import { registerPwa } from './utils/pwa';

if (import.meta.env.PROD) window.addEventListener('load', registerPwa, {once:true});

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
