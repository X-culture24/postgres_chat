// src/pages/Welcome.js
import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function Welcome() {
  const navigate = useNavigate();

  return (
    <div className="text-center mt-5">
      <h1>Welcome to TechHub Chat</h1>
      <p>Connect with devs who share your passion</p>
      <button className="btn btn-primary" onClick={() => navigate('/register')}>
        Get Started
      </button>
    </div>
  );
}
