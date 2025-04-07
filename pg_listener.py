# run.py
import os
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from threading import Thread

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for Flask
CORS(app, resources={r"/*": {"origins": "*"}})

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://gift:gift123@localhost/realtime_app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database connection
db = SQLAlchemy(app)

# Initialize SocketIO with CORS
socketio = SocketIO(app, cors_allowed_origins="*")

# Import listener after app initialization
from listener import start_listener

# Start the listener in a separate thread
@app.before_first_request
def start_pg_listener():
    start_listener()
    print("Started PostgreSQL listener in the background.")

# Routes and app initialization
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app, debug=True)
