import firebase_admin
from firebase_admin import credentials, firestore

# Download service account key from Firebase Console
cred = credentials.Certificate('rfid-access-control-151cd-firebase-adminsdk-fbsvc-6a92a77af2.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

def get_user_by_roll(roll_number):
    """Get user data from Firestore"""
    users_ref = db.collection('users')
    query = users_ref.where('roll_number', '==', roll_number).limit(1)
    docs = query.stream()
    
    for doc in docs:
        return doc.to_dict()
    return None

def save_user_pin(roll_number, pin_hash):
    """Save/update user PIN"""
    user_ref = db.collection('users').document(roll_number)
    user_ref.update({'pin_hash': pin_hash})

def create_user(user_data):
    """Create new user in database"""
    user_ref = db.collection('users').document(user_data['roll_number'])
    user_ref.set(user_data)