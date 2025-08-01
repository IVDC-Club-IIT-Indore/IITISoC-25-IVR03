// Card Dispenser System with ESP32
// Two motors, two IR sensors, L298N motor driver

// Motor Driver L298N Pin Connections
#define MOTOR1_IN1 2   // Motor 1 direction pin 1
#define MOTOR1_IN2 4   // Motor 1 direction pin 2
#define MOTOR1_ENA 5   // Motor 1 speed control (PWM)

#define MOTOR2_IN3 16  // Motor 2 direction pin 1
#define MOTOR2_IN4 17  // Motor 2 direction pin 2
#define MOTOR2_ENB 18  // Motor 2 speed control (PWM)

// IR Sensor Pin Connections
#define IR_SENSOR1 19  // First IR sensor (detects card from stack)
#define IR_SENSOR2 21  // Second IR sensor (detects card at output)

// Manual Control Pin
#define MOTOR2_ENABLE_PIN 22  // Digital input to enable Motor 2 operation

// System States
enum SystemState {
  IDLE,
  DISPENSING_FROM_STACK,
  WAITING_FOR_MOTOR2_ENABLE,  // New state: waiting for manual enable signal
  TRANSPORTING_CARD,
  CARD_DISPENSED
};

SystemState currentState = IDLE;

// Motor speed (0-255)
const int MOTOR_SPEED = 150;

// Timing variables
unsigned long lastDebounceTime1 = 0;
unsigned long lastDebounceTime2 = 0;
const unsigned long DEBOUNCE_DELAY = 50;

// Sensor states
bool sensor1_state = false;
bool sensor2_state = false;
bool last_sensor1_state = false;
bool last_sensor2_state = false;

// Manual control states
bool motor2_enable_signal = false;
bool last_motor2_enable_signal = false;

void setup() {
  Serial.begin(115200);
  
  // Initialize motor driver pins
  pinMode(MOTOR1_IN1, OUTPUT);
  pinMode(MOTOR1_IN2, OUTPUT);
  pinMode(MOTOR1_ENA, OUTPUT);
  
  pinMode(MOTOR2_IN3, OUTPUT);
  pinMode(MOTOR2_IN4, OUTPUT);
  pinMode(MOTOR2_ENB, OUTPUT);
  
  // Initialize IR sensor pins
  pinMode(IR_SENSOR1, INPUT);
  pinMode(IR_SENSOR2, INPUT);
  
  // Initialize manual control pin
  pinMode(MOTOR2_ENABLE_PIN, INPUT_PULLUP);  // Using internal pullup resistor
  
  // Stop both motors initially
  stopMotor1();
  stopMotor2();
  
  Serial.println("Card Dispenser System Initialized");
  Serial.println("Send 'DISPENSE' to start dispensing a card");
  Serial.println("Connect GPIO 22 to GND to enable Motor 2 operation");
}

void loop() {
  // Read sensor states and manual control signal
  readSensors();
  readManualControls();
  
  // Check for serial commands
  if (Serial.available()) {
    String command = Serial.readString();
    command.trim();
    
    if (command.equals("DISPENSE") && currentState == IDLE) {
      startDispensing();
    }
  }
  
  // State machine for card dispensing
  switch (currentState) {
    case IDLE:
      // System waiting for command
      break;
      
    case DISPENSING_FROM_STACK:
      // Motor 1 is running, waiting for IR sensor 1 to detect card
      if (sensor1_state && !last_sensor1_state) {
        Serial.println("Card detected by sensor 1 - Waiting for Motor 2 enable signal");
        stopMotor1();
        currentState = WAITING_FOR_MOTOR2_ENABLE;
      }
      break;
      
    case WAITING_FOR_MOTOR2_ENABLE:
      // Card is ready, waiting for manual enable signal to start Motor 2
      if (motor2_enable_signal && !last_motor2_enable_signal) {
        Serial.println("Motor 2 enable signal received - Starting transport");
        startMotor2();
        currentState = TRANSPORTING_CARD;
      }
      break;
      
    case TRANSPORTING_CARD:
      // Motor 2 is running, waiting for IR sensor 2 to detect card
      if (sensor2_state && !last_sensor2_state) {
        Serial.println("Card detected by sensor 2 - Card dispensed");
        stopMotor2();
        currentState = CARD_DISPENSED;
      }
      break;
      
    case CARD_DISPENSED:
      // Wait a moment then return to idle
      delay(1000);
      Serial.println("Ready for next card");
      currentState = IDLE;
      break;
  }
  
  // Update last sensor and control states
  last_sensor1_state = sensor1_state;
  last_sensor2_state = sensor2_state;
  last_motor2_enable_signal = motor2_enable_signal;
  
  delay(10); // Small delay for stability
}

void readSensors() {
  // Read IR sensors with debouncing
  bool reading1 = digitalRead(IR_SENSOR1);
  bool reading2 = digitalRead(IR_SENSOR2);
  
  // Sensor 1 debouncing
  if (reading1 != last_sensor1_state) {
    lastDebounceTime1 = millis();
  }
  
  if ((millis() - lastDebounceTime1) > DEBOUNCE_DELAY) {
    if (reading1 != sensor1_state) {
      sensor1_state = reading1;
    }
  }
  
  // Sensor 2 debouncing
  if (reading2 != last_sensor2_state) {
    lastDebounceTime2 = millis();
  }
  
  if ((millis() - lastDebounceTime2) > DEBOUNCE_DELAY) {
    if (reading2 != sensor2_state) {
      sensor2_state = reading2;
    }
  }
}

void readManualControls() {
  // Read manual control pin (active LOW due to pullup)
  motor2_enable_signal = !digitalRead(MOTOR2_ENABLE_PIN);
}

void startDispensing() {
  Serial.println("Starting card dispensing...");
  startMotor1();
  currentState = DISPENSING_FROM_STACK;
}

// Motor 1 Control Functions (Stack roller)
void startMotor1() {
  digitalWrite(MOTOR1_IN1, HIGH);
  digitalWrite(MOTOR1_IN2, LOW);
  analogWrite(MOTOR1_ENA, MOTOR_SPEED);
  Serial.println("Motor 1 started (dispensing from stack)");
}

void stopMotor1() {
  digitalWrite(MOTOR1_IN1, LOW);
  digitalWrite(MOTOR1_IN2, LOW);
  analogWrite(MOTOR1_ENA, 0);
  Serial.println("Motor 1 stopped");
}

// Motor 2 Control Functions (Transport roller)
void startMotor2() {
  digitalWrite(MOTOR2_IN3, HIGH);
  digitalWrite(MOTOR2_IN4, LOW);
  analogWrite(MOTOR2_ENB, MOTOR_SPEED);
  Serial.println("Motor 2 started (transporting card)");
}

void stopMotor2() {
  digitalWrite(MOTOR2_IN3, LOW);
  digitalWrite(MOTOR2_IN4, LOW);
  analogWrite(MOTOR2_ENB, 0);
  Serial.println("Motor 2 stopped");
}

// Reverse motor functions (if needed for troubleshooting)
void reverseMotor1() {
  digitalWrite(MOTOR1_IN1, LOW);
  digitalWrite(MOTOR1_IN2, HIGH);
  analogWrite(MOTOR1_ENA, MOTOR_SPEED);
}

void reverseMotor2() {
  digitalWrite(MOTOR2_IN3, LOW);
  digitalWrite(MOTOR2_IN4, HIGH);
  analogWrite(MOTOR2_ENB, MOTOR_SPEED);
}

// Emergency stop function
void emergencyStop() {
  stopMotor1();
  stopMotor2();
  currentState = IDLE;
  Serial.println("Emergency stop activated!");
}
