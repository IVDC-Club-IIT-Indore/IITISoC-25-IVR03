#include <LiquidCrystal_I2C.h>
#include <SPI.h>
#include <MFRC522.h>
#include <FastLED.h>

// LCD Configuration
LiquidCrystal_I2C lcd(0x27, 16, 2);  // 16x2 LCD at I2C address 0x27

// RFID Configuration
#define RST_PIN    34
#define SS_PIN     17
#define OUTPUT_PIN 26
MFRC522 rfid(SS_PIN, RST_PIN);

// LED Configuration
#define LED_PIN 5
#define LED2_PIN 18
#define NUM_LEDS 1
CRGB leds[NUM_LEDS];
CRGB leds2[NUM_LEDS];

// Authorization Configuration
byte authorizedUID[] = {0x24, 0x00, 0x03, 0x02, 0x1}; // 240003021 in hex bytes
const int authorizedUIDSize = 5; // Adjust based on your card's UID size

// Timing variables
unsigned long lastDetectedTime = 0;
unsigned long lastLcdUpdate = 0;
unsigned long timerStartTime = 0;
unsigned long cardInsertTime = 0;
unsigned long lastLedUpdate = 0;
unsigned long accessDeniedTime = 0;
bool timerRunning = false;
bool cardWasPresent = false;
bool cardJustInserted = false;
bool ledState = false;
bool cardEverInserted = false;
bool accessGranted = false;
bool accessDenied = false;
const unsigned long timeoutDuration = 500; // ms for RFID timeout
const unsigned long lcdUpdateInterval = 1000; // ms for LCD update
const unsigned long greenDuration = 5000; // 5 seconds green light
const unsigned long ledBlinkInterval = 500; // LED blink interval
const unsigned long accessDeniedDisplayTime = 3000; // 3 seconds to show access denied

void setup() {
  // Initialize Serial
  Serial.begin(115200);
  
  // Initialize LCD
  initializeLcd();
  
  // Initialize RFID
  initializeRfid();
  
  // Initialize LED
  initializeLed();
  
  Serial.println("System initialized. RFID Access Control active.");
  Serial.print("Authorized Card ID: ");
  printAuthorizedCard();
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
  lcd.print("Hello User");
  lcd.setCursor(0, 1);
  lcd.print("Insert Card...");
  Serial.println("LCD initialized");
}

void initializeRfid() {
  SPI.begin();
  rfid.PCD_Init();
  pinMode(OUTPUT_PIN, OUTPUT);
  digitalWrite(OUTPUT_PIN, LOW);
  Serial.println("RFID initialized - Authorized access only");
}

void initializeLed() {
  pinMode(LED_PIN, OUTPUT);
  pinMode(LED2_PIN, OUTPUT);
  FastLED.addLeds<WS2812, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.addLeds<WS2812, LED2_PIN, GRB>(leds2, NUM_LEDS);
  Serial.println("LEDs initialized");
}

void printAuthorizedCard() {
  for (int i = 0; i < authorizedUIDSize; i++) {
    Serial.print(authorizedUID[i] < 0x10 ? "0" : "");
    Serial.print(authorizedUID[i], HEX);
  }
  Serial.println();
}

bool isAuthorizedCard() {
  // Check if the detected card matches the authorized UID
  if (rfid.uid.size != authorizedUIDSize) {
    return false;
  }
  
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] != authorizedUID[i]) {
      return false;
    }
  }
  return true;
}

void handleRfidDetection() {
  bool cardDetected = false;
  
  if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
    lastDetectedTime = millis();
    cardDetected = true;
    
    Serial.print("Card Detected: ");
    printCardId();
    
    // Check if this is an authorized card
    if (isAuthorizedCard()) {
      // AUTHORIZED ACCESS
      Serial.println("ACCESS GRANTED");
      accessGranted = true;
      accessDenied = false;
      
      // Start timer when authorized card is detected
      if (!timerRunning) {
        timerStartTime = millis();
        cardInsertTime = millis();
        timerRunning = true;
        cardJustInserted = true;
        
        // Display authorized card ID
        if (!cardEverInserted) {
          lcd.clear();
          lcd.print("ACCESS GRANTED");
          lcd.setCursor(0, 1);
          lcd.print("   240003021   ");
          cardEverInserted = true;
        }
        
        Serial.println("Timer started - Authorized card inserted");
      }
    } else {
      // UNAUTHORIZED ACCESS
      Serial.println("ACCESS DENIED - Unauthorized card");
      accessGranted = false;
      accessDenied = true;
      accessDeniedTime = millis();
      
      // Display access denied message
      lcd.clear();
      lcd.print("ACCESS DENIED");
      lcd.setCursor(0, 1);
      lcd.print("Unauthorized");
      
      // Stop any running timer
      if (timerRunning) {
        timerRunning = false;
        cardJustInserted = false;
        Serial.println("Timer stopped - Unauthorized card");
      }
    }
  }
  
  // Check if card is still present
  bool cardPresent = (millis() - lastDetectedTime < timeoutDuration);
  
  // Stop timer when authorized card is removed
  if (timerRunning && !cardPresent && cardWasPresent && accessGranted) {
    timerRunning = false;
    cardJustInserted = false;
    accessGranted = false;
    Serial.println("Timer stopped - Authorized card removed");
    displayCardRemovedMessage();
  }
  
  // Clear access denied message after timeout
  if (accessDenied && (millis() - accessDeniedTime >= accessDeniedDisplayTime)) {
    accessDenied = false;
    displayCardRemovedMessage();
  }
  
  cardWasPresent = cardPresent;
  
  // Control output pin based on authorized card detection only
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
  // Only activate output pin for authorized cards
  if (accessGranted && (millis() - lastDetectedTime < timeoutDuration)) {
    digitalWrite(OUTPUT_PIN, HIGH);
  } else {
    digitalWrite(OUTPUT_PIN, LOW);
  }
}

void updateLcdDisplay() {
  // Update LCD only at specified intervals
  if (millis() - lastLcdUpdate >= lcdUpdateInterval) {
    if (timerRunning && accessGranted) {
      displayTimer();
    }
    lastLcdUpdate = millis();
  }
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
  lcd.clear();
  lcd.print("Hello User");
  lcd.setCursor(0, 1);
  lcd.print("Insert Card...");
  cardEverInserted = false;
}

void updateLedStatus() {
  if (accessDenied) {
    // Show solid red for access denied
    showAccessDeniedLed();
  } else if (!timerRunning || !accessGranted) {
    // Card not inserted or not authorized - blink red
    blinkRedLed();
    // Second LED shows light blue when no authorized access
    showLightBlueLed();
  } else {
    // Authorized card is inserted
    if (cardJustInserted && (millis() - cardInsertTime < greenDuration)) {
      // Show solid green for 5 seconds after authorized card insertion
      showGreenLed();
    } else {
      // After 5 seconds, blink purple
      cardJustInserted = false;
      blinkPurpleLed();
    }
    // Second LED shows warm yellow when authorized card is inserted
    showWarmYellowLed();
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

void showAccessDeniedLed() {
  // Solid red for access denied
  leds[0] = CRGB(255, 0, 0);  // Red
  leds2[0] = CRGB(255, 0, 0); // Both LEDs red for denial
  FastLED.show();
}

void showLightBlueLed() {
  leds2[0] = CRGB(173, 216, 230);  // Light blue
  FastLED.show();
}

void showWarmYellowLed() {
  leds2[0] = CRGB(255, 204, 102);  // Warm yellow
  FastLED.show();
}
