# RFID Access Control System - Flask Web Interface

## Overview
This repository contains a Flask-based web application for an RFID access control system integrated with Firebase. The system provides a web interface to manage access control, user authentication, and device interaction.

## Project Structure
```
├── static/
│   └── images/           # Static assets (logos, icons, etc)
├── templates/            # HTML templates for web pages
├── app.py                # Main Flask application entry point
├── config.py             # Application configuration settings
├── firebase_config.py    # Firebase integration setup
├── models.py             # Database models and schemas
├── requirements.txt      # Python dependencies
├── rfid_handler.py       # RFID device communication module
└── service-account.json  # Firebase Admin SDK credentials
```

## Key Features
- Firebase Realtime Database integration for data storage
- RFID device communication handling
- Web-based management interface
- User authentication system
- Real-time access control monitoring

## Installation
1. Clone the repository:
```bash
git clone https://github.com/DhruvB11/rfid-access-control.git
cd rfid-access-control
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Firebase:
- Create a Firebase project at [firebase.google.com](https://firebase.google.com/)
- Download your service account JSON file and replace `rfid-access-control-151cd-firebase-adminsdk-...`
- Configure Firebase settings in `firebase_config.py`

4. Configure application settings in `config.py`

## Running the Application
```bash
python app.py
```

The web interface will be accessible at:
`http://localhost:5000`

## Dependencies
- Flask (web framework)
- Firebase Admin SDK (Firebase integration)
- Python-dotenv (environment variable management)
- Additional packages listed in `requirements.txt`

## Configuration
Edit these files for custom setup:
- `config.py`: Application settings (secret keys, debug mode)
- `firebase_config.py`: Firebase connection parameters
- `models.py`: Database schema definitions

## Security Notes
- **IMPORTANT**: Never commit service account credentials to version control
- Add `service-account.json` to your `.gitignore` file
- Use environment variables for sensitive configuration
