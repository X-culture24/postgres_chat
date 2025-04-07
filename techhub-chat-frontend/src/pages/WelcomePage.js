import React from 'react';
import { useNavigate } from 'react-router-dom';
import './WelcomePage.css';

function WelcomePage() {
    const navigate = useNavigate(); // Use navigate instead of history

    const handleStart = () => {
        navigate('/register'); // Use navigate to change routes
    };

    return (
        <div className="welcome-container">
            <h1>Welcome to ChatApp</h1>
            <p className="tagline">Connect with your friends in real-time.</p>
            <button className="get-started-btn" onClick={handleStart}>Get Started</button>
        </div>
    );
}

export default WelcomePage;
