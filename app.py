from flask import Flask, request, jsonify, render_template, send_from_directory
from pymongo import MongoClient, ASCENDING
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from bson import ObjectId
import json
import re
import logging
from functools import wraps

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection with retry logic
def get_db_connection():
    try:
        client = MongoClient('mongodb+srv://zeeshanunique2619:RWt5xLFezN8Ggkhm@cluster0.a1ovg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
        db = client['collination']
        # Test connection
        db.command('ping')
        return db
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise

# Database initialization
db = get_db_connection()
users_collection = db['user']

# Create indexes for optimization
users_collection.create_index([("email", ASCENDING)])
users_collection.create_index([("phone_number", ASCENDING)])
users_collection.create_index([("linked_id", ASCENDING)])

def validate_phone_number(phone: str) -> bool:
    """Validate phone number has exactly 10 digits"""
    if not phone:
        return True  # Empty phone number is allowed
    # Remove any non-digit characters
    digits = re.sub(r'\D', '', phone)
    return len(digits) == 10

def validate_request_data(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            data = request.json
            email = data.get('email', '').strip() if data.get('email') else None
            phone = data.get('phoneNumber', '').strip() if data.get('phoneNumber') else None
            
            # Basic validation
            if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                return jsonify({"error": "Invalid email format"}), 400
            
            if phone and not re.match(r"^\+?[\d\s-]{8,}$", phone):
                return jsonify({"error": "Invalid phone number format"}), 400
                
            if not email and not phone:
                return jsonify({"error": "Either email or phone number is required"}), 400
                
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return jsonify({"error": "Invalid request format"}), 400
    return wrapper

def find_all_linked_contacts(contact_ids: List[ObjectId]) -> List[dict]:
    """Find all contacts in the linked chain including primary and secondary"""
    if not contact_ids:
        return []
        
    return list(users_collection.find({
        '$or': [
            {'_id': {'$in': contact_ids}},
            {'linked_id': {'$in': contact_ids}}
        ],
        'deleted_at': None
    }))

def get_or_create_primary_contact(email: str, phone: str) -> Tuple[dict, List[dict]]:
    """Get existing primary contact or create new one"""
    # Find all potentially related contacts
    query = {'$and': [{'deleted_at': None}]}
    conditions = []
    if email:
        conditions.append({'email': email})
    if phone:
        conditions.append({'phone_number': phone})
    if conditions:
        query['$and'].append({'$or': conditions})
    
    existing_contacts = list(users_collection.find(query))
    
    if not existing_contacts:
        # Create new primary contact
        new_contact = {
            'phone_number': phone,
            'email': email,
            'linked_id': None,
            'link_precedence': 'primary',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'deleted_at': None
        }
        result = users_collection.insert_one(new_contact)
        new_contact['_id'] = result.inserted_id
        return new_contact, [new_contact]
        
    # Find or determine primary contact
    primary_contact = next(
        (c for c in existing_contacts if c['link_precedence'] == 'primary'),
        None
    )
    
    if not primary_contact:
        # Convert oldest contact to primary
        oldest_contact = min(existing_contacts, key=lambda x: x['created_at'])
        users_collection.update_one(
            {'_id': oldest_contact['_id']},
            {
                '$set': {
                    'link_precedence': 'primary',
                    'linked_id': None,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        oldest_contact['link_precedence'] = 'primary'
        oldest_contact['linked_id'] = None
        primary_contact = oldest_contact
        
    # Get all related contacts
    all_contacts = find_all_linked_contacts([c['_id'] for c in existing_contacts])
    
    return primary_contact, all_contacts

# Route to serve the HTML file
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/identify', methods=['POST'])
@validate_request_data
def identify():
    try:
        data = request.json
        email = data.get('email', '').strip() if data.get('email') else None
        phone = data.get('phoneNumber', '').strip() if data.get('phoneNumber') else None
        
        # Get or create primary contact and related contacts
        primary_contact, all_contacts = get_or_create_primary_contact(email, phone)
        
        # Check if we need to create a secondary contact
        existing_emails = {c['email'] for c in all_contacts if c.get('email')}
        existing_phones = {c['phone_number'] for c in all_contacts if c.get('phone_number')}
        
        if (email and email not in existing_emails) or (phone and phone not in existing_phones):
            new_secondary = {
                'phone_number': phone,
                'email': email,
                'linked_id': primary_contact['_id'],
                'link_precedence': 'secondary',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'deleted_at': None
            }
            result = users_collection.insert_one(new_secondary)
            new_secondary['_id'] = result.inserted_id
            all_contacts.append(new_secondary)
        
        # Prepare response
        response = {
            "primaryContactId": str(primary_contact['_id']),
            "emails": sorted(list({c['email'] for c in all_contacts if c.get('email')})),
            "phoneNumbers": sorted(list({c['phone_number'] for c in all_contacts if c.get('phone_number')})),
            "secondaryContactIds": sorted([str(c['_id']) for c in all_contacts if c['link_precedence'] == 'secondary'])
        }
        
        return jsonify({"contact": response}), 200
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True)