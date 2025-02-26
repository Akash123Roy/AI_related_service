from flask import Flask, request, jsonify
from pymongo import MongoClient
import os
import logging
from functools import wraps
import jwt
from datetime import datetime, timedelta

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('891477c8c5a959c029a87a94ffaa97784ae1b0c6b093d76ad928e98a53b1928f', 'defaultsecret')

# MongoDB setup
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
client = MongoClient(MONGO_URI)
db = client['microservice_db']
collection = db['data']

# Logger setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Utility function for token verification
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401
        return f(*args, **kwargs)
    return decorated

# Routes
@app.route('/login', methods=['POST'])
def login():
    """Generate JWT token"""
    data = request.json
    if data.get('username') == 'admin' and data.get('password') == 'password':
        token = jwt.encode({'user': data['username'], 'exp': datetime.utcnow() + timedelta(hours=1)}, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token})
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/data', methods=['POST'])
@token_required
def add_data():
    """Insert data into MongoDB"""
    try:
        data = request.json
        if not data:
            return jsonify({'message': 'No data provided!'}), 400
        collection.insert_one(data)
        logger.info('Data inserted successfully')
        return jsonify({'message': 'Data inserted successfully'}), 201
    except Exception as e:
        logger.error(f"Error inserting data: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/data/<string:item_id>', methods=['GET'])
@token_required
def get_data(item_id):
    """Retrieve data from MongoDB"""
    try:
        data = collection.find_one({'_id': item_id})
        if not data:
            return jsonify({'message': 'Item not found'}), 404
        data['_id'] = str(data['_id'])  # Convert ObjectId to string for JSON serialization
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error retrieving data: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/data/<string:item_id>', methods=['PUT'])
@token_required
def update_data(item_id):
    """Update data in MongoDB"""
    try:
        updates = request.json
        if not updates:
            return jsonify({'message': 'No updates provided!'}), 400
        result = collection.update_one({'_id': item_id}, {'$set': updates})
        if result.matched_count == 0:
            return jsonify({'message': 'Item not found'}), 404
        logger.info(f"Data for item {item_id} updated successfully")
        return jsonify({'message': 'Data updated successfully'}), 200
    except Exception as e:
        logger.error(f"Error updating data: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/data/<string:item_id>', methods=['DELETE'])
@token_required
def delete_data(item_id):
    """Delete data from MongoDB"""
    try:
        result = collection.delete_one({'_id': item_id})
        if result.deleted_count == 0:
            return jsonify({'message': 'Item not found'}), 404
        logger.info(f"Data for item {item_id} deleted successfully")
        return jsonify({'message': 'Data deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting data: {e}")
        return jsonify({'message': 'Internal server error'}), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Check if the service is up"""
    return jsonify({'status': 'UP'}), 200

# Main entry point
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
