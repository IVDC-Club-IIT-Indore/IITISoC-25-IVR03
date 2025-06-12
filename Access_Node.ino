#include <SPI.h>
#include <MFRC522.h>

#define RST_PIN    22
#define SS_PIN     21
#define OUTPUT_PIN 26

MFRC522 rfid(SS_PIN, RST_PIN);

unsigned long lastDetectedTime = 0;
const unsigned long timeoutDuration = 500; // ms

void setup() {
  Serial.begin(115200);
  SPI.begin();
  rfid.PCD_Init();
  pinMode(OUTPUT_PIN, OUTPUT);
  digitalWrite(OUTPUT_PIN, LOW);
  Serial.println("Hold RFID card to keep pin 26 HIGH.");
}

void loop() {
  bool cardDetected = false;
  unsigned long cardStartTime = 0;    // Time when card was placed
unsigned long cardHoldTime = 0;

  if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
    lastDetectedTime = millis();
    cardDetected = true;

    Serial.print("Card Detected: ");
    for (byte i = 0; i < rfid.uid.size; i++) {
      Serial.print(rfid.uid.uidByte[i] < 0x10 ? "0" : "");
      Serial.print(rfid.uid.uidByte[i], HEX);
    }
    Serial.println();
  }

  // Keep pin HIGH if card was recently detected
  if (millis() - lastDetectedTime < timeoutDuration) {
    digitalWrite(OUTPUT_PIN, HIGH);
  } else {
    digitalWrite(OUTPUT_PIN, LOW);
  }

  delay(50); // Reduce CPU usage
}
