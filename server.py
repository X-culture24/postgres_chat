from flask import request
from flask_socketio import emit, join_room, leave_room, SocketIO
from run import app  # Assuming you have your Flask app initialized in your_app.py

# This would be your user connections tracking dictionary
user_connections = {}

# Initialize SocketIO with the Flask app
socketio = SocketIO(app)

@socketio.on('connect')
def handle_connect():
    user_id = request.args.get('user_id')  # Get user_id from query parameters
    if user_id:
        user_connections[user_id] = request.sid  # Store the user's connection
        print(f"User {user_id} connected with session ID {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    user_id = request.args.get('user_id')
    if user_id and user_id in user_connections:
        del user_connections[user_id]  # Remove the user from the tracking dictionary
        print(f"User {user_id} disconnected")

@socketio.on('send_message')
def handle_message(data):
    # Here you broadcast the message to all connected users
    emit('receive_message', {'message': data['text']}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
