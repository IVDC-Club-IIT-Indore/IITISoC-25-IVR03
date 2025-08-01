import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    FIREBASE_CREDENTIALS = 'path/to/serviceAccountKey.json'
    RFID_PORT = '/dev/ttyUSB0'  # Adjust for your RFID reader
    RFID_BAUDRATE = 9600