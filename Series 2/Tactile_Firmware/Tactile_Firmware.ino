uint8_t targetPwm[15] = {0};
uint8_t dataIdx = 0;
bool waitingForHeader = true;

uint32_t lastMicros = 0;
uint8_t pwmCounter = 0;

void setup() {
  Serial.begin(115200);
  DDRD |= 0b11111100; // Pins 2-7 (6 channels)
  DDRB |= 0b00111111; // Pins 8-13 (6 channels)
  DDRC |= 0b00000111; // Pins A0-A2 (3 channels) 
  // A4 and A5 remain default INPUT for tactile reading
}

void loop() {
  while (Serial.available() > 0) {
    uint8_t b = Serial.read();
    if (waitingForHeader) {
      if (b == 255) {
        waitingForHeader = false;
        dataIdx = 0;
      }
    } else {
      if (b == 255) {
        dataIdx = 0; // Collision reset
      } else {
        targetPwm[dataIdx++] = b;
        if (dataIdx == 15) {
          waitingForHeader = true;
          
          // Zero-latency tactile intercept
          uint8_t p1 = analogRead(A4) >> 2; // Scale 10-bit to 8-bit
          uint8_t p2 = analogRead(A5) >> 2;
          
          // Reserve 255 strictly for the packet header
          if (p1 == 255) p1 = 254;
          if (p2 == 255) p2 = 254;

          Serial.write(255);
          Serial.write(p1);
          Serial.write(p2);
        }
      }
    }
  }

  uint32_t currentMicros = micros();
  if (currentMicros - lastMicros >= 10) { 
    lastMicros = currentMicros;
    pwmCounter++;
    if (pwmCounter >= 254) pwmCounter = 0; 

    uint8_t portD_mask = 0, portB_mask = 0, portC_mask = 0;

    for (int i = 0; i < 6; i++) {
      if (targetPwm[i] > pwmCounter)     portD_mask |= (1 << (i + 2)); 
      if (targetPwm[i + 6] > pwmCounter) portB_mask |= (1 << i);       
    }
    for (int i = 0; i < 3; i++) {
      if (targetPwm[i + 12] > pwmCounter) portC_mask |= (1 << i);
    }

    PORTD = (PORTD & 0b00000011) | portD_mask;
    PORTB = (PORTB & 0b11000000) | portB_mask;
    PORTC = (PORTC & 0b11111000) | portC_mask;
  }
}