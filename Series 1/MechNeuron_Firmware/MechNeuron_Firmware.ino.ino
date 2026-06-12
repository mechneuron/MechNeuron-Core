// MechNeuron Series 1: The Breathing Matrix Core
// 18-Channel Direct Port Soft-PWM & Framed Serial

uint8_t targetPwm[18] = {0};
uint8_t dataIdx = 0;
bool waitingForHeader = true;

uint32_t lastMicros = 0;
uint8_t pwmCounter = 0;

void setup() {
  Serial.begin(115200);
  
  // Set pins 2-7 (PORTD), 8-13 (PORTB), and A0-A5 (PORTC) as OUTPUT
  DDRD |= 0b11111100; // Pins 2-7
  DDRB |= 0b00111111; // Pins 8-13
  DDRC |= 0b00111111; // Pins A0-A5
}

void loop() {
  // 1. Unbreakable Serial State Machine (Non-blocking)
  while (Serial.available() > 0) {
    uint8_t b = Serial.read();
    
    if (waitingForHeader) {
      if (b == 255) {
        waitingForHeader = false;
        dataIdx = 0;
      }
    } else {
      if (b == 255) {
        // Frame collision detected, reset alignment
        dataIdx = 0;
      } else {
        targetPwm[dataIdx++] = b;
        if (dataIdx == 18) {
          waitingForHeader = true;
          Serial.write('A'); // Transmit ACK to Python
        }
      }
    }
  }

  // 2. High-Frequency Direct Port Manipulation PWM (Zero delay)
  uint32_t currentMicros = micros();
  if (currentMicros - lastMicros >= 10) { 
    lastMicros = currentMicros;
    pwmCounter++;
    if (pwmCounter >= 254) pwmCounter = 0; // Match Python's 0-254 range

    uint8_t portD_mask = 0;
    uint8_t portB_mask = 0;
    uint8_t portC_mask = 0;

    // Bitwise computation for all 18 channels
    for (int i = 0; i < 6; i++) {
      if (targetPwm[i] > pwmCounter)      portD_mask |= (1 << (i + 2)); 
      if (targetPwm[i + 6] > pwmCounter)  portB_mask |= (1 << i);       
      if (targetPwm[i + 12] > pwmCounter) portC_mask |= (1 << i);       
    }

    // Apply masks, preserving system pins (RX/TX, XTAL)
    PORTD = (PORTD & 0b00000011) | portD_mask;
    PORTB = (PORTB & 0b11000000) | portB_mask;
    PORTC = (PORTC & 0b11000000) | portC_mask;
  }
}