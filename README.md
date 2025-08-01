# IITISoC-25-IVR003: RFID-Based Machine Logging and Access Control System

Team Members

_**Team Member 1**:  [Dhruv Bhardwaj](https://github.com/DhruvB11)_

_**Team Member 2**:  [Atharva Chavan](https://github.com/athrvchavan)_

Mentors

_**Mentor 1**:  [Satyajeet Pani](https://github.com/mentor1)_

_**Mentor 2**:  [Tejas Bhavekar](https://github.com/Tejker)_

_**Mentor 3**:  [Saket Jaiswal](https://github.com/mentor3)_

# RFID Access Control System

A comprehensive RFID-based access control system consisting of multiple interconnected components for machine access management in maker spaces, laboratories, or industrial environments.

##  System Architecture

This system consists of four main components:

1. **Issuing Station** - Web-based interface for card programming and user management
2. **Access Nodes** - RFID readers at individual machines for access control
3. **MQTT Communication** - Real-time messaging between components
4. **Card Dispenser** - Automated card dispensing mechanism

##  Table of Contents

- [System Components](#system-components)
- [Features](#features)
- [Hardware Requirements](#hardware-requirements)
- [Installation & Setup](#installation--setup)
- [Usage Guide](#usage-guide)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

##  System Components

### 1. Issuing Station
**Location**: `Issuing Station/`

A Flask-based web application that serves as the central hub for RFID card management.

**Key Features:**
- Web-based kiosk interface for card issuing
- Firebase Firestore integration for user data storage
- Real-time RFID card detection and writing
- User authentication with PIN verification
- Machine access permission management
- Responsive design optimized for touch interfaces

**Main Files:**
- `app.py` - Main Flask application
- `rfid_handler.py` - MFRC522 RFID reader interface
- `firebase_config.py` - Firebase database integration
- `templates/index.html` - Web interface

### 2. Access Nodes
**Location**: `MQTT/esp32_clients/`

ESP32-based RFID readers deployed at individual machines to control access.

**Key Features:**
- RFID card reading and validation
- MQTT communication with central system
- Real-time access logging
- LED/buzzer feedback for access status
- WiFi connectivity with auto-reconnection
- Configurable machine permissions

**Components:**
- ESP32 microcontroller
- MFRC522 RFID reader module
- Status indicators (LEDs)
- MQTT client for communication

### 3. MQTT Communication System
**Location**: `MQTT/rpi_mqtt_clients/`

Facilitates real-time communication between all system components.

**Features:**
- Centralized message broker (Raspberry Pi)
- Publish/Subscribe architecture
- Real-time access event logging
- System status monitoring
- Scalable to multiple access nodes

**Files:**
- `client_pub` - Publisher client example
- `client_sub` - Subscriber client with callbacks

### 4. Card Dispenser
**Location**: `dispenser_code.ino`

Automated card dispensing system for seamless card distribution.

**Features:**
- Dual motor control (stack roller & transport roller)
- IR sensor-based card detection
- Manual enable control for Motor 2
- State machine-based operation
- Serial command interface

##  Features

### Core Functionality
- **Multi-Machine Access Control**: Manage access to multiple machines/stations
- **User Management**: Store user profiles with roll numbers, names, branches
- **Permission Matrix**: Flexible machine access permissions per user
- **Real-Time Monitoring**: Live tracking of access events across all nodes
- **Secure Authentication**: PIN-based user verification
- **Card Programming**: Write user data and permissions directly to RFID cards

### Advanced Features
- **Web-Based Interface**: Intuitive kiosk-style interface for card issuing
- **Firebase Integration**: Cloud-based user data storage and synchronization
- **MQTT Messaging**: Real-time communication between all system components
- **Auto Card Detection**: Automatic card presence detection and processing
- **Session Management**: Unique session IDs for tracking and auditing
- **Scalable Architecture**: Easy addition of new access nodes and machines

## 🛠️ Hardware Requirements

### Issuing Station
- Raspberry Pi 4 (recommended) or compatible SBC
- MFRC522 RFID Reader/Writer module
- 7" Touchscreen display (optional, for kiosk mode)
- MicroSD card (32GB+)
- Power supply (5V, 3A+)

### Access Nodes (per machine)
- ESP32 Development Board
- MFRC522 RFID Reader module
- LEDs for status indication
- Buzzer (optional)
- Breadboard/PCB for connections
- Power supply (5V, 1A)

### Card Dispenser
- ESP32 Development Board
- L298N Motor Driver
- 2x DC Motors (12V recommended)
- 2x IR Sensors
- Manual enable switch/button
- Power supply (12V for motors, 5V for ESP32)

### General
- RFID Cards (MIFARE Classic 1K)
- WiFi Router/Access Point
- Jumper wires and connectors

##  Installation & Setup

### 1. Issuing Station Setup

#### Prerequisites
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
sudo apt install python3-pip python3-venv git -y

# Enable SPI for RFID communication
sudo raspi-config
# Navigate to: Interfacing Options > SPI > Enable
```

#### Installation
```bash
# Clone repository
git clone <repository-url>
cd IITISoC-25-IVR03-main/Issuing\ Station/

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Firebase Setup
1. Create a Firebase project at [firebase.google.com](https://firebase.google.com/)
2. Enable Firestore Database
3. Generate service account key:
   - Go to Project Settings > Service Accounts
   - Generate new private key
   - Save as `service-account.json` in the project directory
4. Update `firebase_config.py` with your credentials

#### Hardware Connections (MFRC522 to Raspberry Pi)
```
MFRC522    Raspberry Pi
VCC    ->  3.3V
RST    ->  GPIO 25
GND    ->  GND
MISO   ->  GPIO 9 (MISO)
MOSI   ->  GPIO 10 (MOSI)
SCK    ->  GPIO 11 (SCLK)
SDA    ->  GPIO 8 (CE0)
```

#### Run Application
```bash
python app.py
```
Access the web interface at: `http://localhost:5000`

### 2. Access Node Setup

#### Arduino IDE Configuration
1. Install ESP32 board package in Arduino IDE
2. Install required libraries:
   - `WiFi` (built-in)
   - `PubSubClient` for MQTT

#### Hardware Connections (MFRC522 to ESP32)
```
MFRC522    ESP32
VCC    ->  3.3V
RST    ->  GPIO 22
GND    ->  GND
MISO   ->  GPIO 19
MOSI   ->  GPIO 23
SCK    ->  GPIO 18
SDA    ->  GPIO 21
```

#### Programming
1. Open `MQTT/esp32_clients/esp_mqtt_client1/esp_mqtt_client1.ino`
2. Update WiFi credentials and MQTT broker IP
3. Upload to ESP32

### 3. MQTT Broker Setup

#### Install Mosquitto on Raspberry Pi
```bash
sudo apt install mosquitto mosquitto-clients -y
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

#### Test MQTT Communication
```bash
# Terminal 1 - Subscribe
mosquitto_sub -h localhost -t "test/topic"

# Terminal 2 - Publish
mosquitto_pub -h localhost -t "test/topic" -m "Hello MQTT"
```

### 4. Card Dispenser Setup

#### Hardware Connections
```
L298N Motor Driver    ESP32
VCC              ->   5V
GND              ->   GND
IN1              ->   GPIO 2
IN2              ->   GPIO 4
ENA              ->   GPIO 5
IN3              ->   GPIO 16
IN4              ->   GPIO 17
ENB              ->   GPIO 18

IR Sensors       ESP32
Sensor 1 OUT     ->   GPIO 19
Sensor 2 OUT     ->   GPIO 21
VCC              ->   5V
GND              ->   GND

Manual Control   ESP32
Enable Switch    ->   GPIO 22 (with pullup)
```

#### Programming
1. Open `dispenser_code.ino` in Arduino IDE
2. Upload to ESP32
3. Open Serial Monitor for debugging

##  Usage Guide

### Card Issuing Process

1. **Start System**: Access the web interface on the issuing station
2. **Insert Card**: Place RFID card on the reader - system auto-detects
3. **Enter Roll Number**: Use on-screen interface to input student/employee ID
4. **PIN Verification**: Enter 4-digit PIN for authentication
5. **Verify Details**: Review user information and accessible machines
6. **Write Card**: System programs the card with user permissions
7. **Card Ready**: Remove programmed card from reader

### Access Control Process

1. **Approach Machine**: User approaches machine with programmed RFID card
2. **Card Scan**: Place card near access node RFID reader
3. **Permission Check**: System verifies card data and machine permissions
4. **Access Granted/Denied**: LED indicators and/or buzzer provide feedback
5. **Machine Access**: If authorized, user can operate the machine
6. **Session Logging**: All access attempts are logged via MQTT

### Card Dispensing Process

1. **Load Cards**: Place blank RFID cards in the dispenser stack
2. **Initiate Dispensing**: Send "DISPENSE" command via serial interface
3. **Automatic Operation**: 
   - Motor 1 dispenses card from stack
   - System waits for manual enable signal
   - Motor 2 transports card to output slot
4. **Card Retrieved**: User collects dispensed card

##  API Documentation

### Issuing Station API Endpoints

#### `GET /api/card_status`
Check if RFID card is detected
```json
{
  "detected": true,
  "card_id": "123456789"
}
```

#### `POST /api/check_user`
Verify if user exists in database
```json
// Request
{
  "roll_number": "2021001"
}

// Response
{
  "exists": true,
  "has_pin": true,
  "user_data": {
    "name": "John Doe",
    "branch": "Computer Science",
    "year": "3rd Year"
  }
}
```

#### `POST /api/verify_pin`
Authenticate user with PIN
```json
// Request
{
  "roll_number": "2021001",
  "pin": "1234"
}

// Response
{
  "valid": true,
  "user_data": {
    "name": "John Doe",
    "accessible_machines": ["3D Printer", "Laser Cutter"]
  }
}
```

#### `POST /api/write_card`
Program RFID card with user data
```json
// Request
{
  "roll_number": "2021001"
}

// Response
{
  "success": true,
  "message": "Card written successfully",
  "card_id": "123456789"
}
```

### MQTT Topics

#### Access Control Topics
- `access/machine/{machine_id}/request` - Access request from user
- `access/machine/{machine_id}/response` - Access granted/denied response
- `access/machine/{machine_id}/log` - Access event logging

#### System Status Topics
- `system/status/issuing_station` - Issuing station health status
- `system/status/access_node/{node_id}` - Individual access node status
- `system/broadcast` - System-wide announcements

##  Configuration

### Issuing Station Configuration (`config.py`)
```python
class Config:
    SECRET_KEY = 'your-secret-key-here'
    FIREBASE_CREDENTIALS = 'path/to/service-account.json'
    RFID_PORT = '/dev/ttyUSB0'  # Adjust for your setup
    RFID_BAUDRATE = 9600
```

### Firebase Database Structure
```javascript
// Collection: users
{
  "roll_number": "2021001",
  "name": "John Doe",
  "branch": "Computer Science", 
  "year": "3rd Year",
  "pin_hash": "hashed_pin_string",
  "accessible_machines": ["3D Printer", "Laser Cutter"],
  "card_id": "123456789",
  "created_at": "timestamp",
  "last_updated": "timestamp"
}
```

### Machine ID Mapping
```python
machine_id_map = {
    '3D Printer': 1,
    'Laser Cutter': 2,
    'CNC Machine': 3,
    'PCB Mill': 4,
    'Soldering Station': 5,
    'Drill Press': 6,
    'Band Saw': 7,
    'Lathe': 8,
    # Add more machines as needed (up to 16 total)
}
```

##  Troubleshooting

### Common Issues

#### RFID Reader Not Detected
- **Check Connections**: Verify all SPI connections are secure
- **Enable SPI**: Ensure SPI is enabled in Raspberry Pi configuration
- **Power Supply**: Check 3.3V power supply to MFRC522 module
- **GPIO Conflicts**: Ensure no other processes are using SPI pins

#### Firebase Connection Issues
- **Service Account**: Verify service account JSON file is valid and accessible
- **Internet Connection**: Check network connectivity to Firebase servers
- **Firestore Rules**: Ensure database security rules allow read/write access
- **Project Configuration**: Verify Firebase project ID and settings

#### MQTT Communication Problems
- **Broker Status**: Check if Mosquitto broker is running (`sudo systemctl status mosquitto`)
- **Network Configuration**: Verify IP addresses and port 1883 accessibility
- **Client Authentication**: Check MQTT client credentials if authentication is enabled
- **Firewall**: Ensure port 1883 is not blocked by firewall rules

#### Card Writing Failures
- **Card Compatibility**: Use MIFARE Classic 1K cards only
- **Card Positioning**: Ensure card is properly positioned on reader
- **Authentication**: Verify default MIFARE keys (0xFF x 6) work
- **Memory Blocks**: Check if target memory blocks are accessible

### Debug Commands

#### Test RFID Reader
```python
# Run in Issuing Station directory
python -c "from rfid_handler import RFIDHandler; h = RFIDHandler(); print(h.detect_card())"
```

#### Test Firebase Connection
```python
# Run in Issuing Station directory  
python -c "from firebase_config import get_user_by_roll; print(get_user_by_roll('test123'))"
```

#### Test MQTT Publisher
```bash
mosquitto_pub -h localhost -t "test/topic" -m "test message"
```

#### Test MQTT Subscriber
```bash
mosquitto_sub -h localhost -t "test/topic"
```

##  Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines for Python code
- Use meaningful commit messages
- Add comments for complex logic
- Test hardware integrations thoroughly
- Update documentation for new features

##  License

This project is licensed under the MIT License - see the LICENSE file for details.

##  Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Check existing documentation and troubleshooting guides
- Verify hardware connections and configurations

##  Future Enhancements

- **Mobile App**: iOS/Android app for remote management
- **Biometric Integration**: Fingerprint/face recognition for additional security
- **Usage Analytics**: Detailed reporting and usage statistics
- **Remote Configuration**: Over-the-air configuration updates
- **Multi-Tenant Support**: Support for multiple organizations/departments
- **Backup Systems**: Automatic data backup and recovery mechanisms

