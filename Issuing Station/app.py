from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import threading
import time
import traceback
from firebase_config import get_user_by_roll
from models import hash_pin, verify_pin
from rfid_handler import RFIDHandler

app = Flask(__name__)
CORS(app)

# Initialize RFID handler
rfid = RFIDHandler()  
current_card_id = None
card_detection_active = False
detection_lock = threading.Lock()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/card_status')
def card_status():
    """Check if card is detected"""
    global current_card_id
    try:
        # Only check for card when not continuously polling
        with detection_lock:
            card_id = rfid.detect_card()
            if card_id != current_card_id:
                current_card_id = card_id
                if card_id:
                    print(f"New card detected: {card_id}")
                else:
                    print("Card removed")
            
            return jsonify({
                'detected': bool(current_card_id),
                'card_id': current_card_id
            })
    except Exception as e:
        print(f"Card status error: {e}")
        return jsonify({'detected': False, 'error': str(e)})

@app.route('/api/start_detection')
def start_detection():
    """Start active card detection for card writing"""
    global card_detection_active
    card_detection_active = True
    return jsonify({'status': 'Detection started'})

@app.route('/api/stop_detection') 
def stop_detection():
    """Stop active card detection"""
    global card_detection_active
    card_detection_active = False
    return jsonify({'status': 'Detection stopped'})

@app.route('/api/check_user', methods=['POST'])
def check_user():
    """Check if user exists in database"""
    try:
        data = request.json
        roll_number = data.get('roll_number')
        
        if not roll_number:
            return jsonify({'exists': False, 'error': 'Roll number required'})
        
        user = get_user_by_roll(roll_number)
        if user:
            return jsonify({
                'exists': True,
                'has_pin': bool(user.get('pin_hash')),
                'user_data': {
                    'name': user.get('name', ''),
                    'branch': user.get('branch', ''),
                    'year': user.get('year', '')
                }
            })
        else:
            return jsonify({'exists': False})
            
    except Exception as e:
        print(f"Check user error: {e}")
        traceback.print_exc()
        return jsonify({'exists': False, 'error': str(e)})

@app.route('/api/verify_pin', methods=['POST'])
def verify_pin_route():
    """Verify user PIN"""
    try:
        data = request.json
        roll_number = data.get('roll_number')
        pin = data.get('pin')
        
        if not roll_number or not pin:
            return jsonify({'valid': False, 'error': 'Roll number and PIN required'})
        
        user = get_user_by_roll(roll_number)
        if user and user.get('pin_hash') and verify_pin(pin, user.get('pin_hash')):
            return jsonify({
                'valid': True,
                'user_data': {
                    'name': user.get('name', ''),
                    'branch': user.get('branch', ''),
                    'year': user.get('year', ''),
                    'accessible_machines': user.get('accessible_machines', [])
                }
            })
        else:
            return jsonify({'valid': False, 'error': 'Invalid PIN'})
            
    except Exception as e:
        print(f"Verify PIN error: {e}")
        traceback.print_exc()
        return jsonify({'valid': False, 'error': str(e)})

@app.route('/api/write_card', methods=['POST'])
def write_card():
    """Write data to RFID card with enhanced debugging"""
    global current_card_id
    try:
        data = request.json
        roll_number = data.get('roll_number')
        
        print(f"Write card request for roll: {roll_number}")
        
        if not roll_number:
            return jsonify({'success': False, 'error': 'Roll number required'})
        
        # Check card presence multiple times
        with detection_lock:
            card_present = False
            for attempt in range(3):
                if rfid.is_card_present():
                    card_present = True
                    break
                time.sleep(0.3)
                
            if not card_present:
                return jsonify({'success': False, 'error': 'No card detected. Please place card on reader.'})
            
            current_card_id = rfid.detect_card()
            if not current_card_id:
                return jsonify({'success': False, 'error': 'Unable to read card ID'})
        
        # Get user data
        user = get_user_by_roll(roll_number)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'})
        
        # FIX: Proper machine ID mapping
        accessible_machines = user.get('accessible_machines', [])
        machine_flags = '0' * 16
        
        # Define machine name to ID mapping
        machine_id_map = {
            '3D Printer': 1,
            'Laser Cutter': 2,
            'CNC Machine': 3,
            'PCB Mill': 4,
            'Soldering Station': 5,
            # Add more as needed
        }
        
        print(f"Accessible machines: {accessible_machines}")
        
        for machine in accessible_machines:
            try:
                if isinstance(machine, str):
                    machine_id = machine_id_map.get(machine)
                else:
                    machine_id = int(machine)
                
                if machine_id and 1 <= machine_id <= 16:
                    bit_position = machine_id - 1
                    machine_flags = machine_flags[:bit_position] + '1' + machine_flags[bit_position+1:]
                    print(f"Set bit {bit_position} for machine {machine}")
                    
            except (ValueError, TypeError) as e:
                print(f"Error processing machine {machine}: {e}")
                continue
        
        print(f"Final machine flags: {machine_flags}")
        
        # Write to card
        success, message = rfid.write_card(roll_number, machine_flags)
        
        if success:
            # Update database
            try:
                from firebase_config import db
                user_ref = db.collection('users').document(roll_number)
                user_ref.update({
                    'card_id': str(current_card_id),
                    'card_written_at': time.time()
                })
            except Exception as db_error:
                print(f"Database update error: {db_error}")
            
            return jsonify({
                'success': True, 
                'message': 'Card written successfully',
                'card_id': current_card_id
            })
        else:
            return jsonify({'success': False, 'error': f'Failed to write card: {message}'})
            
    except Exception as e:
        print(f"Write card error: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/api/read_card', methods=['GET'])
def read_card():
    """Read current card data"""
    try:
        with detection_lock:
            card_data = rfid.read_card()
            if card_data:
                return jsonify({'success': True, 'data': card_data})
            else:
                return jsonify({'success': False, 'error': 'No card detected or read failed'})
    except Exception as e:
        print(f"Read card error: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Controlled card detection thread - only runs when needed
def controlled_card_detection():
    global current_card_id, card_detection_active
    last_card_id = None
    
    while True:
        try:
            if card_detection_active:
                with detection_lock:
                    card_id = rfid.detect_card()
                    if card_id != last_card_id:
                        current_card_id = card_id
                        last_card_id = card_id
                        if card_id:
                            print(f"Card detected in active mode: {card_id}")
                        else:
                            print("Card removed in active mode")
            
            time.sleep(0.5)  # Check every 500ms instead of continuous polling
            
        except Exception as e:
            print(f"Detection thread error: {e}")
            time.sleep(1)

if __name__ == '__main__':
    try:
        # Start controlled card detection
        detection_thread = threading.Thread(target=controlled_card_detection)
        detection_thread.daemon = True
        detection_thread.start()
        
        print("RFID Card Station starting...")
        print("Access the interface at: http://localhost:5000")
        
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        rfid.cleanup()