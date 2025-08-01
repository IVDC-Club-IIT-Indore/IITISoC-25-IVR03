# Firebase Firestore structure
"""
Collection: users
Document ID: roll_number
Fields:
{
    'roll_number': '2021001',
    'name': 'John Doe',
    'branch': 'Computer Science',
    'year': '3rd Year',
    'pin_hash': 'hashed_pin_here',
    'accessible_machines': ['3D Printer', 'Laser Cutter'],
    'card_id': 'written_card_id',
    'created_at': timestamp,
    'last_updated': timestamp
}
"""

import hashlib
import datetime

def hash_pin(pin):
    """Hash PIN for secure storage"""
    return hashlib.sha256(pin.encode()).hexdigest()

def verify_pin(pin, pin_hash):
    """Verify PIN against stored hash"""
    return hash_pin(pin) == pin_hash

def create_user_data(roll_number, name, branch, year, machines, pin):
    """Create user data structure"""
    return {
        'roll_number': roll_number,
        'name': name,
        'branch': branch,
        'year': year,
        'pin_hash': hash_pin(pin),
        'accessible_machines': machines,
        'card_id': None,
        'created_at': datetime.datetime.now(),
        'last_updated': datetime.datetime.now()
    }