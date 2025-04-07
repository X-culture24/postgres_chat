import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask app
app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://gift:gift123@localhost/realtime_app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database connection
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Unified endpoint for User registration and login

# Register route
@app.route('/user', methods=['POST'])
def register_or_login():
    data = request.get_json()
    
    # Check if we are registering a new user or logging in
    if 'password' in data:
        # Registration Logic
        if 'name' not in data or 'email' not in data:
            return jsonify({"error": "Missing data"}), 400
        
        # Check if the user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({"error": "User already exists"}), 400
        
        # Store the password in plain text (not hashed)
        password = data['password']

        # Create a new user
        new_user = User(name=data['name'], email=data['email'], password=password)

        try:
            db.session.add(new_user)
            db.session.commit()
            return jsonify({"message": "User created successfully", "user": {"id": new_user.id, "name": new_user.name, "email": new_user.email}}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    
    else:
        # Login Logic
        if 'email' not in data or 'password' not in data:
            return jsonify({"error": "Missing login data"}), 400
        
        # Find the user by email
        user = User.query.filter_by(email=data['email']).first()

        if user and user.password == data['password']:  # Direct comparison of passwords
            return jsonify({"message": "Login successful", "user": {"id": user.id, "name": user.name, "email": user.email}}), 200
        else:
            return jsonify({"error": "Invalid email or password"}), 401


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
