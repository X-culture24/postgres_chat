import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom'; // Corrected: useNavigate
import './ChatPage.css';

function ChatPage() {
    const [message, setMessage] = useState('');
    const [messages, setMessages] = useState([]);
    const navigate = useNavigate(); // Corrected: use navigate instead of useHistory

    const handleSendMessage = async () => {
        try {
            const response = await axios.post('http://localhost:5000/send_message', {
                message,
            });
            setMessages([...messages, { sender: 'You', text: message }]);
            setMessage('');
        } catch (error) {
            console.error('Error sending message:', error);
        }
    };

    const handleBack = () => {
        navigate('/register'); // Corrected: use navigate for redirection
    };

    return (
        <div className="chat-container">
            <div className="chat-header">
                <h2>Chat with Lawrence</h2>
                <button className="back-btn" onClick={handleBack}>←</button>
            </div>
            <div className="chat-bubbles">
                {messages.map((msg, index) => (
                    <div className={`message ${msg.sender === 'You' ? 'sender' : 'receiver'}`} key={index}>
                        <span>{msg.text}</span>
                    </div>
                ))}
            </div>
            <div className="message-input">
                <input
                    type="text"
                    placeholder="Type a message..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                />
                <button onClick={handleSendMessage}>Send</button>
            </div>
        </div>
    );
}

export default ChatPage;
