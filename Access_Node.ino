#include <LiquidCrystal_I2C.h>
#include <SPI.h>
#include <MFRC522.h>
#include <FastLED.h>

// LCD Configuration
LiquidCrystal_I2C lcd(0x27, 16, 2);  // 16x2 LCD at I2C address 0x27

// RFID Configuration
#define RST_PIN    22
#define SS_PIN     21
#define OUTPUT_PIN 26
MFRC522 rfid(SS_PIN, RST_PIN);

// LED Configuration
#define LED_PIN 5
#define NUM_LEDS 1
CRGB leds[NUM_LEDS];

// Timing variables
unsigned long lastDetectedTime = 0;
unsigned long lastLcdUpdate = 0;
unsigned long timerStartTime = 0;
unsigned long cardInsertTime = 0;
unsigned long lastLedUpdate = 0;
bool timerRunning = false;
bool cardWasPresent = false;
bool cardJustInserted = false;
bool ledState = false;
String cardData = "No Card Data";
const unsigned long timeoutDuration = 500; // ms for RFID timeout
const unsigned long lcdUpdateInterval = 1000; // ms for LCD update
const unsigned long greenDuration = 5000; // 5 seconds green light
const unsigned long ledBlinkInterval = 500; // LED blink interval

void setup() {
  // Initialize Serial
  Serial.begin(115200);
  
  // Initialize LCD
  initializeLcd();
  
  // Initialize RFID
  initializeRfid();
  
  // Initialize LED
  initializeLed();
  
  Serial.println("System initialized. LCD Timer, RFID Reader, and LED active.");
}

void loop() {
  // Handle RFID detection
  handleRfidDetection();
  
  // Update LCD display
  updateLcdDisplay();
  
  // Update LED status
  updateLedStatus();
  
  delay(50); // Small delay to reduce CPU usage
}

void initializeLcd() {
  lcd.begin();
  lcd.backlight();
  lcd.print("Waiting for card");
  lcd.setCursor(0, 1);
  lcd.print("Insert Card...");
  Serial.println("LCD initialized");
}

void initializeRfid() {
  SPI.begin();
  rfid.PCD_Init();
  pinMode(OUTPUT_PIN, OUTPUT);
  digitalWrite(OUTPUT_PIN, LOW);
  Serial.println("RFID initialized - Hold card to keep pin 26 HIGH");
}

void initializeLed() {
  pinMode(LED_PIN, OUTPUT);
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  Serial.println("LED initialized");
}

void handleRfidDetection() {
  bool cardDetected = false;
  
  if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
    lastDetectedTime = millis();
    cardDetected = true;
    
    // Start timer when card is first detected
    if (!timerRunning) {
      timerStartTime = millis();
      cardInsertTime = millis();
      timerRunning = true;
      cardJustInserted = true;
      
      // Read card data from sector 0 block 4
      readCardData();
      
      Serial.println("Timer started - Card inserted");
    }
    
    Serial.print("Card Detected: ");
    printCardId();
  }
  
  // Check if card is still present
  bool cardPresent = (millis() - lastDetectedTime < timeoutDuration);
  
  // Stop timer when card is removed
  if (timerRunning && !cardPresent && cardWasPresent) {
    timerRunning = false;
    cardJustInserted = false;
    cardData = "No Card Data";
    Serial.println("Timer stopped - Card removed");
    displayCardRemovedMessage();
  }
  
  cardWasPresent = cardPresent;
  
  // Control output pin based on card detection
  controlOutputPin();
}

void printCardId() {
  for (byte i = 0; i < rfid.uid.size; i++) {
    Serial.print(rfid.uid.uidByte[i] < 0x10 ? "0" : "");
    Serial.print(rfid.uid.uidByte[i], HEX);
  }
  Serial.println();
}

void controlOutputPin() {
  if (millis() - lastDetectedTime < timeoutDuration) {
    digitalWrite(OUTPUT_PIN, HIGH);
  } else {
    digitalWrite(OUTPUT_PIN, LOW);
  }
}

void updateLcdDisplay() {
  // Update LCD only at specified intervals
  if (millis() - lastLcdUpdate >= lcdUpdateInterval) {
    if (timerRunning) {
      displayCardDataAndTimer();
    }
    lastLcdUpdate = millis();
  }
}
void displayCardDataAndTimer() {
  // Display card data on first row
  lcd.setCursor(0, 0);
  lcd.print("                ");
  lcd.setCursor(0, 0);
  lcd.print(cardData);
  
  // Display timer on second row
  unsigned long elapsedTime = (millis() - timerStartTime) / 1000;
  unsigned int minutes = elapsedTime / 60;
  unsigned int seconds = elapsedTime % 60;
  
  lcd.setCursor(0, 1);
  lcd.print("                ");
  lcd.setCursor(0, 1);
  lcd.print("  ");
  lcd.print(minutes);
  lcd.print(" MIN ");
  lcd.print(seconds);
  lcd.print(" SEC");
}

void displayTimer() {
  unsigned long elapsedTime = (millis() - timerStartTime) / 1000;
  unsigned int minutes = elapsedTime / 60;
  unsigned int seconds = elapsedTime % 60;
  
  lcd.setCursor(0, 1);
  // Clear the second row first to avoid leftover characters
  lcd.print("                ");
  lcd.setCursor(0, 1);
  lcd.print("  ");
  lcd.print(minutes);
  lcd.print(" MIN ");
  lcd.print(seconds);
  lcd.print(" SEC");
}

void displayCardRemovedMessage() {
  lcd.setCursor(0, 0);
  lcd.print("                ");
  lcd.setCursor(0, 0);
  lcd.print("Waiting for card");
  lcd.setCursor(0, 1);
  lcd.print("                ");
  lcd.setCursor(0, 1);
  lcd.print("Insert Card...");
}

void readCardData() {
  MFRC522::MIFARE_Key key;
  for (byte i = 0; i < 6; i++) key.keyByte[i] = 0xFF; // Default key
  
  byte block = 4; // Block 4 in sector 0
  byte buffer[18];
  byte size = sizeof(buffer);
  
  // Authenticate using key A
  MFRC522::StatusCode status = rfid.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, block, &key, &(rfid.uid));
  
  if (status == MFRC522::STATUS_OK) {
    // Read the block
    status = rfid.MIFARE_Read(block, buffer, &size);
    if (status == MFRC522::STATUS_OK) {
      // Extract first 9 characters
      cardData = "";
      for (int i = 0; i < 9 && i < 16; i++) {
        if (buffer[i] >= 32 && buffer[i] <= 126) { // Printable ASCII characters
          cardData += (char)buffer[i];
        } else {
          cardData += "?"; // Replace non-printable characters
        }
      }
      Serial.print("Card Data Read: ");
      Serial.println(cardData);
    } else {
      cardData = "Read Error";
      Serial.println("Failed to read block 4");
    }
  } else {
    cardData = "Auth Error";
    Serial.println("Authentication failed for block 4");
  }
  
  // Halt communication
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
}

void updateLedStatus() {
  if (!timerRunning) {
    // Card not inserted - blink red
    blinkRedLed();
  } else {
    // Card is inserted
    if (cardJustInserted && (millis() - cardInsertTime < greenDuration)) {
      // Show solid green for 5 seconds after card insertion
      showGreenLed();
    } else {
      // After 5 seconds, blink purple
      cardJustInserted = false;
      blinkPurpleLed();
    }
  }
}

void blinkRedLed() {
  if (millis() - lastLedUpdate >= ledBlinkInterval) {
    ledState = !ledState;
    if (ledState) {
      leds[0] = CRGB(255, 0, 0);  // Red
    } else {
      leds[0] = CRGB(0, 0, 0);    // Off
    }
    FastLED.show();
    lastLedUpdate = millis();
  }
}

void showGreenLed() {
  leds[0] = CRGB(0, 255, 0);  // Green
  FastLED.show();
}

void blinkPurpleLed() {
  if (millis() - lastLedUpdate >= ledBlinkInterval) {
    ledState = !ledState;
    if (ledState) {
      leds[0] = CRGB(128, 0, 128);  // Purple
    } else {
      leds[0] = CRGB(0, 0, 0);      // Off
    }
    FastLED.show();
    lastLedUpdate = millis();
  }
}
