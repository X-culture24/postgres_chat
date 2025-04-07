from flask import request, jsonify
from app import app, db
from models import User

# Register route
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Check if the user already exists
    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({"message": "User already exists!"}), 400

    # Create a new user with plain text password
    new_user = User(username=data['username'], email=data['email'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully!"}), 201

# Login route
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    # Check if the user exists
    user = User.query.filter_by(username=data['username']).first()
    if not user:
        return jsonify({"message": "User not found!"}), 404

    # Verify the password (no hashing here, just a plain text comparison)
    if data['password'] != user.password:
        return jsonify({"message": "Invalid password!"}), 401

    return jsonify({"message": "Login successful!"}), 200
