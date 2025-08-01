# Simplified rfid_handler.py with reliable card writing using spidev and gpiozero
import spidev
import time
import uuid
from gpiozero import DigitalOutputDevice

# MFRC522 constants
COMMAND_REG = 0x01 << 1
FIFO_DATA_REG = 0x09 << 1
FIFO_LEVEL_REG = 0x0A << 1
CONTROL_REG = 0x0C << 1
BIT_FRAMING_REG = 0x0D << 1
TX_CONTROL_REG = 0x14 << 1
ERROR_REG = 0x06 << 1
STATUS1_REG = 0x07 << 1
STATUS2_REG = 0x08 << 1
COLL_REG = 0x0E << 1
TX_ASK_REG = 0x15 << 1
MODE_REG = 0x11 << 1
TIMER_MODE_REG = 0x2A << 1
TIMER_PRESCALER_REG = 0x2B << 1
TIMER_RELOAD_REG_H = 0x2C << 1
TIMER_RELOAD_REG_L = 0x2D << 1
TX_AUTO_REG = 0x16 << 1
RX_GAIN_REG = 0x26 << 1
RF_CFG_REG = 0x26 << 1
CRC_RESULT_REG_M = 0x21 << 1
CRC_RESULT_REG_L = 0x22 << 1

# Commands
COMMAND_IDLE = 0x00
COMMAND_MEM = 0x01
COMMAND_CALCULATE_CRC = 0x03
COMMAND_TRANSMIT = 0x04
COMMAND_RECEIVE = 0x08
COMMAND_TRANSCEIVE = 0x0C
COMMAND_MFAUTHENT = 0x0E
COMMAND_SOFTRESET = 0x0F

# PICC commands
PICC_REQIDL = 0x26
PICC_REQALL = 0x52
PICC_ANTICOLL = 0x93
PICC_SElECTTAG = 0x93
PICC_AUTHENT1A = 0x60
PICC_AUTHENT1B = 0x61
PICC_READ = 0x30
PICC_WRITE = 0xA0
PICC_DECREMENT = 0xC0
PICC_INCREMENT = 0xC1
PICC_RESTORE = 0xC2
PICC_TRANSFER = 0xB0
PICC_HALT = 0x50

# Return codes
MI_OK = 0
MI_NOTAGERR = 1
MI_ERR = 2

class MFRC522:
    def __init__(self, rst_pin=25):
        self.rst = DigitalOutputDevice(rst_pin)
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 1000000
        self.spi.mode = 0
        self.PICC_REQIDL = PICC_REQIDL
        self.PICC_REQALL = PICC_REQALL
        self.PICC_ANTICOLL = PICC_ANTICOLL
        self.PICC_SElECTTAG = PICC_SElECTTAG
        self.PICC_AUTHENT1A = PICC_AUTHENT1A
        self.PICC_AUTHENT1B = PICC_AUTHENT1B
        self.PICC_READ = PICC_READ
        self.PICC_WRITE = PICC_WRITE
        self.PICC_HALT = PICC_HALT
        self.MI_OK = MI_OK
        self.MI_NOTAGERR = MI_NOTAGERR
        self.MI_ERR = MI_ERR
        
        # Reset the chip
        self.rst.on()
        time.sleep(0.1)
        self.rst.off()
        time.sleep(0.1)
        self.rst.on()
        time.sleep(0.1)

    def write_reg(self, reg, val):
        self.spi.xfer2([reg & 0x7E, val])

    def read_reg(self, reg):
        val = self.spi.xfer2([reg | 0x80, 0])[1]
        return val

    def set_bit_mask(self, reg, mask):
        tmp = self.read_reg(reg)
        self.write_reg(reg, tmp | mask)

    def clear_bit_mask(self, reg, mask):
        tmp = self.read_reg(reg)
        self.write_reg(reg, tmp & (~mask))

    def MFRC522_Init(self):
        # Reset
        self.write_reg(COMMAND_REG, COMMAND_SOFTRESET)
        time.sleep(0.01)
        
        # Timer: auto timer with 25ms timeout
        self.write_reg(TIMER_MODE_REG, 0x8D)
        self.write_reg(TIMER_PRESCALER_REG, 0x3E)
        self.write_reg(TIMER_RELOAD_REG_L, 30)
        self.write_reg(TIMER_RELOAD_REG_H, 0)
        
        # Default 0x00. Force 100% ASK modulation
        self.write_reg(TX_AUTO_REG, 0x40)
        
        # Set CRC preset value to 0x6363
        self.write_reg(MODE_REG, 0x3D)
        
        # Enable antenna
        self.write_reg(TX_CONTROL_REG, 0x83)

    def MFRC522_Request(self, req_mode):
        TagType = []
        self.write_reg(BIT_FRAMING_REG, 0x07)
        TagType.append(req_mode)
        (status, back_data, back_len) = self.MFRC522_ToCard(COMMAND_TRANSCEIVE, TagType)
        
        if ((status != MI_OK) | (back_len != 0x10)):
            status = MI_ERR
            
        return (status, back_data)

    def MFRC522_Anticoll(self):
        back_data = []
        ser_num_check = 0
        
        ser_num = []
        
        self.write_reg(BIT_FRAMING_REG, 0x00)
        
        ser_num.append(PICC_ANTICOLL)
        ser_num.append(0x20)
        
        (status, back_data, back_len) = self.MFRC522_ToCard(COMMAND_TRANSCEIVE, ser_num)
        
        if(status == MI_OK):
            i = 0
            if len(back_data) == 5:
                while i < 4:
                    ser_num_check = ser_num_check ^ back_data[i]
                    i = i + 1
                if ser_num_check != back_data[i]:
                    status = MI_ERR
            else:
                status = MI_ERR
                
        return (status, back_data)

    def MFRC522_ToCard(self, command, send_data):
        back_data = []
        back_len = 0
        status = MI_ERR
        irq_en = 0x00
        wait_irq = 0x00
        last_bits = None
        n = 0
        i = 0
        
        if command == COMMAND_MFAUTHENT:
            irq_en = 0x12
            wait_irq = 0x10
        elif command == COMMAND_TRANSCEIVE:
            irq_en = 0x77
            wait_irq = 0x30
            
        self.write_reg(0x02, irq_en | 0x80)
        self.clear_bit_mask(0x04, 0x80)
        self.set_bit_mask(FIFO_LEVEL_REG, 0x80)
        
        self.write_reg(COMMAND_REG, COMMAND_IDLE)
        
        while(i < len(send_data)):
            self.write_reg(FIFO_DATA_REG, send_data[i])
            i = i + 1
            
        self.write_reg(COMMAND_REG, command)
            
        if command == COMMAND_TRANSCEIVE:
            self.set_bit_mask(BIT_FRAMING_REG, 0x80)
            
        i = 2000
        while True:
            n = self.read_reg(0x04)
            i = i - 1
            if ~((i != 0) and ~(n & 0x01) and ~(n & wait_irq)):
                break
                
        self.clear_bit_mask(BIT_FRAMING_REG, 0x80)
        
        if i != 0:
            if (self.read_reg(ERROR_REG) & 0x1B) == 0x00:
                status = MI_OK
                
                if n & irq_en & 0x01:
                    status = MI_NOTAGERR
                    
                if command == COMMAND_TRANSCEIVE:
                    n = self.read_reg(FIFO_LEVEL_REG)
                    last_bits = self.read_reg(CONTROL_REG) & 0x07
                    if last_bits != 0:
                        back_len = (n - 1) * 8 + last_bits
                    else:
                        back_len = n * 8
                        
                    if n == 0:
                        n = 1
                    if n > 16:
                        n = 16
                        
                    i = 0
                    while i < n:
                        back_data.append(self.read_reg(FIFO_DATA_REG))
                        i = i + 1
            else:
                status = MI_ERR
        
        return (status, back_data, back_len)

    def MFRC522_SelectTag(self, ser_num):
        back_data = []
        buf = []
        buf.append(PICC_SElECTTAG)
        buf.append(0x70)
        i = 0
        while i < 5:
            buf.append(ser_num[i])
            i = i + 1
        pout = self.CalulateCRC(buf)
        buf.append(pout[0])
        buf.append(pout[1])
        (status, back_data, back_len) = self.MFRC522_ToCard(COMMAND_TRANSCEIVE, buf)
        
        if (status == MI_OK) and (back_len == 0x18):
            return back_data[0]
        else:
            return 0

    def MFRC522_Auth(self, auth_mode, block_addr, sect_key, ser_num):
        buff = []
        buff.append(auth_mode)
        buff.append(block_addr)
        
        i = 0
        while(i < len(sect_key)):
            buff.append(sect_key[i])
            i = i + 1
            
        i = 0
        while(i < 4):
            buff.append(ser_num[i])
            i = i + 1
            
        (status, back_data, back_len) = self.MFRC522_ToCard(COMMAND_MFAUTHENT, buff)
        
        if not (status == MI_OK):
            print("AUTH ERROR!!")
        if not (self.read_reg(STATUS2_REG) & 0x08) != 0:
            print("AUTH ERROR(status2reg & 0x08) != 0")
            
        return status

    def MFRC522_StopCrypto1(self):
        self.clear_bit_mask(STATUS2_REG, 0x08)

    def MFRC522_Read(self, block_addr):
        recvData = []
        recvData.append(PICC_READ)
        recvData.append(block_addr)
        pout = self.CalulateCRC(recvData)
        recvData.append(pout[0])
        recvData.append(pout[1])
        (status, back_data, back_len) = self.MFRC522_ToCard(COMMAND_TRANSCEIVE, recvData)
        if not(status == MI_OK):
            print("Error while reading!")
        i = 0
        if len(back_data) == 16:
            return back_data
        else:
            return None

    def MFRC522_Write(self, block_addr, write_data):
        buff = []
        buff.append(PICC_WRITE)
        buff.append(block_addr)
        crc = self.CalulateCRC(buff)
        buff.append(crc[0])
        buff.append(crc[1])
        (status, back_data, back_len) = self.MFRC522_ToCard(COMMAND_TRANSCEIVE, buff)
        if not(status == MI_OK) or not(back_len == 4) or not((back_data[0] & 0x0F) == 0x0A):
            status = MI_ERR
            
        if status == MI_OK:
            i = 0
            buf = []
            while i < 16:
                buf.append(write_data[i])
                i = i + 1
            crc = self.CalulateCRC(buf)
            buf.append(crc[0])
            buf.append(crc[1])
            (status, back_data, back_len) = self.MFRC522_ToCard(COMMAND_TRANSCEIVE, buf)
            if not(status == MI_OK) or not(back_len == 4) or not((back_data[0] & 0x0F) == 0x0A):
                print("Error while writing")
                status = MI_ERR
        return status

    def CalulateCRC(self, pIndata):
        self.clear_bit_mask(0x05, 0x04)
        self.set_bit_mask(FIFO_LEVEL_REG, 0x80)
        i = 0
        while i < len(pIndata):
            self.write_reg(FIFO_DATA_REG, pIndata[i])
            i = i + 1
        self.write_reg(COMMAND_REG, COMMAND_CALCULATE_CRC)
        i = 0xFF
        while True:
            n = self.read_reg(0x05)
            i = i - 1
            if not ((i != 0) and not (n & 0x04)):
                break
        pOutData = []
        pOutData.append(self.read_reg(CRC_RESULT_REG_L))
        pOutData.append(self.read_reg(CRC_RESULT_REG_M))
        return pOutData

    def cleanup(self):
        self.spi.close()
        self.rst.close()

class SimpleMFRC522:
    def __init__(self):
        self.mfrc = MFRC522()
        self.mfrc.MFRC522_Init()

    def read(self):
        id_val = None
        text = None
        
        (status, TagType) = self.mfrc.MFRC522_Request(self.mfrc.PICC_REQIDL)
        if status == self.mfrc.MI_OK:
            (status, uid) = self.mfrc.MFRC522_Anticoll()
            if status == self.mfrc.MI_OK:
                # Calculate card ID
                card_id = 0
                for i in range(len(uid)):
                    card_id = (card_id << 8) + uid[i]
                id_val = card_id
                
                # Read text from sector 1, block 1
                size = self.mfrc.MFRC522_SelectTag(uid)
                if size > 0:
                    key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
                    if self.mfrc.MFRC522_Auth(self.mfrc.PICC_AUTHENT1A, 4, key, uid) == self.mfrc.MI_OK:
                        text_data = self.mfrc.MFRC522_Read(4)
                        if text_data:
                            text = ''.join(chr(b) for b in text_data if b != 0)
                        self.mfrc.MFRC522_StopCrypto1()
                        
        return id_val, text

    def write(self, text):
        id_val = None
        
        (status, TagType) = self.mfrc.MFRC522_Request(self.mfrc.PICC_REQIDL)
        if status == self.mfrc.MI_OK:
            (status, uid) = self.mfrc.MFRC522_Anticoll()
            if status == self.mfrc.MI_OK:
                # Calculate card ID
                card_id = 0
                for i in range(len(uid)):
                    card_id = (card_id << 8) + uid[i]
                id_val = card_id
                
                # Write text to sector 1, block 1
                size = self.mfrc.MFRC522_SelectTag(uid)
                if size > 0:
                    key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
                    if self.mfrc.MFRC522_Auth(self.mfrc.PICC_AUTHENT1A, 4, key, uid) == self.mfrc.MI_OK:
                        # Prepare text data (16 bytes)
                        text_data = list(text.ljust(16, '\x00')[:16].encode('utf-8'))
                        if self.mfrc.MFRC522_Write(4, text_data) == self.mfrc.MI_OK:
                            print("Write successful")
                        else:
                            print("Write failed")
                        self.mfrc.MFRC522_StopCrypto1()
                        
        return id_val

class RFIDHandler:
    def __init__(self):
        """Initialize RFID reader with simple configuration"""
        self.reader = SimpleMFRC522()
        self.mfrc = self.reader.mfrc
        self.current_card_id = None
        self.last_detection_time = 0
        self.detection_cooldown = 0.5
        
        # Data block assignments for clean organization
        self.ROLL_BLOCK = 8      # Block 8 for roll number
        self.MACHINE_BLOCK = 9   # Block 9 for machine access flags
        self.SESSION_BLOCK = 10  # Block 10 for session ID and timestamp
        
        print("RFID Handler initialized with simplified write structure")
    
    def detect_card(self):
        """Simple card detection with cooldown"""
        try:
            current_time = time.time()
            if current_time - self.last_detection_time < self.detection_cooldown:
                return self.current_card_id
            
            (status, _) = self.mfrc.MFRC522_Request(self.mfrc.PICC_REQIDL)
            if status != self.mfrc.MI_OK:
                if self.current_card_id is not None:
                    print("Card removed")
                    self.current_card_id = None
                return None
            
            (status, uid) = self.mfrc.MFRC522_Anticoll()
            if status != self.mfrc.MI_OK:
                return None
            
            # Convert UID to card ID
            card_id = 0
            for i in range(len(uid)):
                card_id = (card_id << 8) + uid[i]
            
            if self.current_card_id != card_id:
                print(f"Card detected: {card_id}")
                self.current_card_id = card_id
                self.last_detection_time = current_time
            
            return self.current_card_id
            
        except Exception as e:
            print(f"Card detection error: {e}")
            return None
    
    def is_card_present(self):
        """Quick card presence check"""
        try:
            (status, _) = self.mfrc.MFRC522_Request(self.mfrc.PICC_REQIDL)
            return status == self.mfrc.MI_OK
        except Exception as e:
            print(f"Card presence check error: {e}")
            return False
    
    def write_card(self, roll_number, machine_flags):
        """
        Simplified card writing with three data blocks:
        - Block 8: Roll number (16 bytes)
        - Block 9: Machine flags (16 bytes, first 16 chars are the binary flags)
        - Block 10: Session ID + timestamp (16 bytes)
        """
        print(f"Starting card write - Roll: {roll_number}, Flags: {machine_flags}")
        
        # Input validation
        if not roll_number or not str(roll_number).strip():
            return False, "Roll number is required"
        
        if not machine_flags or len(machine_flags) != 16:
            return False, f"Machine flags must be exactly 16 characters (got {len(machine_flags) if machine_flags else 0})"
        
        if not all(c in '01' for c in machine_flags):
            return False, "Machine flags must contain only 0s and 1s"
        
        # Check card presence
        if not self.is_card_present():
            return False, "No card detected"
        
        try:
            # Generate unique session ID (8 chars) + timestamp (8 chars)
            session_id = str(uuid.uuid4())[:8].upper()
            timestamp = str(int(time.time()))[:8]
            session_data = f"{session_id}{timestamp}"
            
            print(f"Generated session data: {session_data}")
            
            # Prepare data for each block
            roll_data = str(roll_number).ljust(16, '\x00')[:16]  # Pad to 16 bytes
            machine_data = machine_flags.ljust(16, '0')[:16]     # Pad to 16 bytes  
            session_data = session_data.ljust(16, '\x00')[:16]   # Pad to 16 bytes
            
            # Attempt card write with retries
            max_attempts = 3
            for attempt in range(max_attempts):
                print(f"Write attempt {attempt + 1}/{max_attempts}")
                
                if self._write_all_blocks(roll_data, machine_data, session_data):
                    print("Card write successful!")
                    return True, f"Card written successfully (Session: {session_id})"
                
                if attempt < max_attempts - 1:
                    print("Write failed, retrying...")
                    time.sleep(1)
            
            return False, "Failed to write after multiple attempts"
            
        except Exception as e:
            print(f"Card write exception: {e}")
            return False, f"Write error: {str(e)}"
    
    def _write_all_blocks(self, roll_data, machine_data, session_data):
        """Write data to all three blocks in sequence"""
        try:
            # Get card UID
            (status, _) = self.mfrc.MFRC522_Request(self.mfrc.PICC_REQIDL)
            if status != self.mfrc.MI_OK:
                print("Failed to request card")
                return False
            
            (status, uid) = self.mfrc.MFRC522_Anticoll()
            if status != self.mfrc.MI_OK:
                print("Failed to get card UID")
                return False
            
            # Select card
            size = self.mfrc.MFRC522_SelectTag(uid)
            if size <= 0:
                print("Failed to select card")
                return False
            
            print(f"Card selected, size: {size}")
            
            # Write each block
            blocks_data = [
                (self.ROLL_BLOCK, roll_data, "Roll Number"),
                (self.MACHINE_BLOCK, machine_data, "Machine Flags"), 
                (self.SESSION_BLOCK, session_data, "Session Data")
            ]
            
            for block_num, data, description in blocks_data:
                if not self._write_single_block(uid, block_num, data, description):
                    return False
                time.sleep(0.1)  # Small delay between block writes
            
            # Verify the write
            print("Verifying written data...")
            return self._verify_all_blocks(uid, roll_data, machine_data, session_data)
            
        except Exception as e:
            print(f"Write blocks exception: {e}")
            return False
    
    def _write_single_block(self, uid, block_num, data, description):
        """Write data to a single block"""
        try:
            # Default MIFARE key
            key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
            
            # Authenticate
            status = self.mfrc.MFRC522_Auth(self.mfrc.PICC_AUTHENT1A, block_num, key, uid)
            if status != self.mfrc.MI_OK:
                print(f"Authentication failed for block {block_num} ({description})")
                return False
            
            # Convert data to bytes
            data_bytes = [ord(c) for c in data]
            
            # Write block
            status = self.mfrc.MFRC522_Write(block_num, data_bytes)
            if status != self.mfrc.MI_OK:
                print(f"Write failed for block {block_num} ({description})")
                return False
            
            print(f"Successfully wrote block {block_num} ({description})")
            return True
            
        except Exception as e:
            print(f"Single block write error for block {block_num}: {e}")
            return False
    
    def _verify_all_blocks(self, uid, expected_roll, expected_machine, expected_session):
        """Verify that all blocks were written correctly"""
        try:
            key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
            
            # Verify each block
            blocks_to_verify = [
                (self.ROLL_BLOCK, expected_roll, "Roll"),
                (self.MACHINE_BLOCK, expected_machine, "Machine"),
                (self.SESSION_BLOCK, expected_session, "Session")
            ]
            
            for block_num, expected_data, description in blocks_to_verify:
                # Authenticate
                status = self.mfrc.MFRC522_Auth(self.mfrc.PICC_AUTHENT1A, block_num, key, uid)
                if status != self.mfrc.MI_OK:
                    print(f"Verification auth failed for {description} block")
                    return False
                
                # Read block
                read_data = self.mfrc.MFRC522_Read(block_num)
                if not read_data:
                    print(f"Verification read failed for {description} block")
                    return False
                
                # Convert to string and compare
                read_string = ''.join(chr(b) for b in read_data[:16])
                expected_clean = expected_data.rstrip('\x00')
                read_clean = read_string.rstrip('\x00')
                
                if read_clean != expected_clean:
                    print(f"Verification failed for {description}: expected '{expected_clean}', got '{read_clean}'")
                    return False
                    
                print(f"Verification passed for {description} block")
            
            print("All blocks verified successfully!")
            return True
            
        except Exception as e:
            print(f"Verification exception: {e}")
            return False
    
    def read_card(self):
        """Read all data from the card"""
        if not self.is_card_present():
            print("No card present for reading")
            return None
        
        try:
            # Get basic card info
            id_val, _ = self.reader.read()
            
            # Read our custom blocks
            (status, _) = self.mfrc.MFRC522_Request(self.mfrc.PICC_REQIDL)
            if status != self.mfrc.MI_OK:
                return {'card_id': id_val, 'error': 'Failed to request card'}
            
            (status, uid) = self.mfrc.MFRC522_Anticoll()
            if status != self.mfrc.MI_OK:
                return {'card_id': id_val, 'error': 'Failed to get UID'}
            
            key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
            result = {'card_id': id_val}
            
            # Read each block
            blocks_to_read = [
                (self.ROLL_BLOCK, 'roll_number'),
                (self.MACHINE_BLOCK, 'machine_flags'),
                (self.SESSION_BLOCK, 'session_data')
            ]
            
            for block_num, field_name in blocks_to_read:
                try:
                    status = self.mfrc.MFRC522_Auth(self.mfrc.PICC_AUTHENT1A, block_num, key, uid)
                    if status == self.mfrc.MI_OK:
                        data = self.mfrc.MFRC522_Read(block_num)
                        if data:
                            value = ''.join(chr(b) for b in data[:16] if b != 0)
                            result[field_name] = value.strip('\x00')
                        else:
                            result[field_name] = ''
                    else:
                        result[field_name] = ''
                except Exception as e:
                    print(f"Error reading block {block_num}: {e}")
                    result[field_name] = ''
            
            # Parse session data if available
            if 'session_data' in result and len(result['session_data']) >= 16:
                session_info = result['session_data']
                result['session_id'] = session_info[:8]
                result['timestamp'] = session_info[8:16]
            
            print(f"Card read result: {result}")
            return result
            
        except Exception as e:
            print(f"Card read error: {e}")
            return {'card_id': id_val if 'id_val' in locals() else None, 'error': str(e)}
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.mfrc.cleanup()
            print("RFID cleanup completed")
        except Exception as e:
            print(f"Cleanup error: {e}")

# Helper function to convert machine list to binary flags
def machines_to_flags(accessible_machines):
    """
    Convert list of machine names/IDs to 16-bit binary string
    Machine ID mapping (you can modify this as needed):
    """
    machine_id_map = {
        '3D Printer': 1,
        'Laser Cutter': 2, 
        'CNC Machine': 3,
        'PCB Mill': 4,
        'Soldering Station': 5,
        'Drill Press': 6,
        'Band Saw': 7,
        'Lathe': 8,
        'Milling Machine': 9,
        'Plasma Cutter': 10,
        # Add more machines as needed, up to 16 total
    }
    
    flags = ['0'] * 16  # Initialize all bits to 0
    
    for machine in accessible_machines:
        try:
            if isinstance(machine, str):
                machine_id = machine_id_map.get(machine)
            else:
                machine_id = int(machine)
            
            if machine_id and 1 <= machine_id <= 16:
                flags[machine_id - 1] = '1'  # Set the corresponding bit
                
        except (ValueError, TypeError):
            print(f"Warning: Could not process machine: {machine}")
            continue
    
    return ''.join(flags)

# Example usage
if __name__ == "__main__":
    handler = RFIDHandler()
    
    try:
        print("Place your RFID card near the reader...")
        
        while True:
            card_id = handler.detect_card()
            if card_id:
                print(f"Card detected: {card_id}")
                
                # Example: write some data to the card
                machine_flags = machines_to_flags(['3D Printer', 'Laser Cutter'])
                success, message = handler.write_card("12345", machine_flags)
                print(f"Write result: {success}, {message}")
                
                # Read the card
                data = handler.read_card()
                if data:
                    print(f"Card data: {data}")
                
                time.sleep(2)  # Wait before next detection
            else:
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        handler.cleanup()