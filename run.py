import os
import logging
import time
from threading import Thread
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, join_room, emit
from flask_cors import CORS
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from flask_migrate import Migrate
import json

# Initialize Flask app
app = Flask(__name__, template_folder='templates')

# Enable CORS for all origins
CORS(app)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://gift:gift123@localhost/realtime_app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and socket
db = SQLAlchemy(app)
migrate = Migrate(app, db)

socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Configure logging to match Werkzeug's format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)
logger = logging.getLogger(__name__)

# ------------------- Models -------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    interest = db.Column(db.String(100), nullable=True)

# ------------------- Frontend Routes -------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

# ------------------- API Routes -------------------
@app.route('/user', methods=['POST'])
def register():
    data = request.get_json()
    logger.info(f"POST /user - Data: {data}")

    if 'password' not in data or 'name' not in data or 'email' not in data:
        logger.warning("Missing required fields")
        return jsonify({"error": "Missing data"}), 400

    if User.query.filter_by(email=data['email']).first():
        logger.warning(f"User already exists: {data['email']}")
        return jsonify({"error": "User already exists"}), 400

    new_user = User(
        name=data['name'],
        email=data['email'],
        password=data['password'],
        interest=data.get('interest')
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        logger.info(f"User created: {new_user.name} ({new_user.email})")
        return jsonify({
            "message": "User created successfully",
            "user": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email,
                "interest": new_user.interest
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating user: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/users', methods=['GET'])
def get_users_by_interest():
    interest = request.args.get('interest')
    logger.info(f"GET /users?interest={interest}")

    if not interest:
        logger.warning("Interest parameter missing")
        return jsonify({"error": "Interest is required"}), 400

    users = User.query.filter_by(interest=interest).all()
    logger.info(f"Found {len(users)} users with interest {interest}")
    return jsonify({
        "users": [
            {"id": u.id, "name": u.name, "email": u.email, "interest": u.interest}
            for u in users
        ]
    }), 200

@app.route('/send_message', methods=['POST'])
def http_send_message():
    data = request.get_json()
    logger.info(f"POST /send_message - Data: {data}")
    
    required_fields = ['sender_id', 'recipient_id', 'message']
    if not all(field in data for field in required_fields):
        logger.warning("Missing required fields")
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        conn = psycopg2.connect("postgresql://gift:gift123@localhost/realtime_app")
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        payload = json.dumps({
            'event': 'new_message',
            'data': {
                'sender_id': data['sender_id'],
                'recipient_id': data['recipient_id'],
                'message': data['message'],
                'timestamp': datetime.now().isoformat()
            }
        })
        
        cur.execute(f"NOTIFY chat_channel, '{payload}'")
        conn.close()
        logger.info("Message notification sent via PostgreSQL")
        return jsonify({"status": "Message sent and notification triggered"}), 200
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return jsonify({"error": str(e)}), 500

# ------------------- SocketIO Events -------------------
@socketio.on('connect')
def handle_connect():
    user_id = request.args.get('user_id')
    if user_id:
        join_room(f"user_{user_id}")
        join_room('global_chat')
        logger.info(f"User {user_id} connected to SocketIO")
        emit('connection_ack', {'status': 'connected', 'user_id': user_id})
    else:
        logger.warning("User ID not provided on SocketIO connect")

@socketio.on('send_message')
def handle_send_message(data):
    logger.info(f"SocketIO message received: {data}")
    
    required_fields = ['sender_id', 'recipient_id', 'message']
    if not all(field in data for field in required_fields):
        logger.warning("Missing fields in SocketIO message")
        return emit('error', {'error': 'Missing required fields'})
    
    timestamp = datetime.now().isoformat()
    
    try:
        conn = psycopg2.connect("postgresql://gift:gift123@localhost/realtime_app")
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        payload = json.dumps({
            'event': 'socket_message',
            'data': {
                **data,
                'timestamp': timestamp
            }
        })
        
        cur.execute(f"NOTIFY chat_channel, '{payload}'")
        conn.close()
        logger.info("SocketIO message forwarded via PostgreSQL")
    except Exception as e:
        logger.error(f"Error forwarding SocketIO message: {e}")

# ------------------- PostgreSQL Listener -------------------
class PGListener:
    def __init__(self, dsn):
        self.dsn = dsn
        self.conn = None
        self.running = False
        
    def connect(self):
        logger.info("Connecting to PostgreSQL...")
        self.conn = psycopg2.connect(self.dsn)
        self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        logger.info("PostgreSQL connection established")
        
    def listen(self):
        self.running = True
        while self.running:
            try:
                if not self.conn or self.conn.closed:
                    self.connect()
                
                cur = self.conn.cursor()
                cur.execute("LISTEN chat_channel;")
                
                self.conn.poll()
                while self.conn.notifies:
                    notify = self.conn.notifies.pop()
                    logger.info(f"PostgreSQL notification received: {notify.payload}")
                    self.handle_notification(notify)
                
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"PostgreSQL listener error: {e}")
                time.sleep(5)
                try:
                    if self.conn:
                        self.conn.close()
                except:
                    pass
                self.connect()
    
    def handle_notification(self, notify):
        try:
            payload = json.loads(notify.payload)
            event_type = payload.get('event')
            data = payload.get('data', {})
            
            if event_type in ['new_message', 'socket_message']:
                logger.info(f"Dispatching message to user {data['recipient_id']}")
                socketio.emit('receive_message', {
                    'sender_id': data['sender_id'],
                    'message': data['message'],
                    'timestamp': data['timestamp']
                }, room=f"user_{data['recipient_id']}")
                
                socketio.emit('chat_activity', {
                    'event': 'message_sent',
                    'from': data['sender_id'],
                    'to': data['recipient_id'],
                    'content': data['message'],
                    'timestamp': data['timestamp']
                }, room='global_chat')
                
        except Exception as e:
            logger.error(f"Error handling notification: {e}")

def start_listener():
    listener = PGListener("postgresql://gift:gift123@localhost/realtime_app")
    listener_thread = Thread(target=listener.listen)
    listener_thread.daemon = True
    listener_thread.start()
    logger.info("PostgreSQL listener thread started")
    return listener

# ------------------- Main Entry -------------------
if __name__ == '__main__':
    logger.info("Starting application...")
    listener = start_listener()
    
    with app.app_context():
        logger.info("Initializing database...")
        db.create_all()
    
    socketio.run(app, debug=True, host='0.0.0.0')