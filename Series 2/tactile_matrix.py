import numpy as np
import serial
import time
import sys

PORT = 'COM6' # Ensure this matches your setup
BAUD_RATE = 115200

try:
    ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
    time.sleep(2) 
except Exception as e:
    print(f"HARDWARE FAULT: Could not connect to {PORT}. {e}")
    sys.exit(1)

# ---------------------------------------------------------
# STRUCTURAL OVERRIDE: Eradicating Asymmetry & Noise
# ---------------------------------------------------------
np.random.seed(42)

# 1. Deterministic Layer 1 Weights
# We explicitly force P1 (A4) and P2 (A5) to have equal, intersecting influence.
W1 = np.array([
    [ 3.0, -3.0,  1.5, -1.5], # Absolute Authority Vector for P1
    [ 1.5,  1.5, -3.0, -3.0]  # Absolute Authority Vector for P2
])
b1 = np.zeros(4)     

# Layer 2 remains pseudorandom for aesthetic complexity
W2 = np.random.randn(4, 15) * 3.0 
b2 = np.random.randn(15) * 0.5    

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

ema_state = np.zeros(15)
ALPHA = 0.08 

# 2. Input Anti-Jitter Filter
# A dedicated EMA to crush organic electromagnetic noise from the potentiometers
input_ema = np.zeros(2)
INPUT_ALPHA = 0.05 

print("Initiating Balanced & Sanitized Tactile Override. Press Ctrl+C to terminate.")
print("-" * 60)

ser.reset_input_buffer()
ser.reset_output_buffer()

try:
    ser.write(bytearray([255]) + bytearray([0]*15))

    while True:
        if ser.in_waiting >= 3:
            header = ser.read(1)
            if header == b'\xff':
                pot_data = ser.read(2)
                
                pot1_raw = pot_data[0]
                pot2_raw = pot_data[1]
                
                sys.stdout.write(f"\r[SYS] TELEMETRY | P1 (A4): {pot1_raw:03d} | P2 (A5): {pot2_raw:03d}   ")
                sys.stdout.flush()
                
                # Mathematical Expansion
                target_p1 = (pot1_raw / 254.0) * 3.0 - 1.5
                target_p2 = (pot2_raw / 254.0) * 3.0 - 1.5
                
                # Jitter Eradication (Input EMA)
                raw_inputs = np.array([target_p1, target_p2])
                input_ema = INPUT_ALPHA * raw_inputs + (1 - INPUT_ALPHA) * input_ema
                
                # Forward Pass
                input_node = np.array([input_ema]) 
                latent = sigmoid(np.dot(input_node, W1) + b1)
                output = sigmoid(np.dot(latent, W2) + b2)[0] 
                
                # Dynamic Range Force
                out_min = np.min(output)
                out_max = np.max(output)
                if out_max > out_min:
                    normalized_output = (output - out_min) / (out_max - out_min)
                else:
                    normalized_output = output
                    
                target = normalized_output * 254
                
                # Visual Cinematic Smoothing
                ema_state = ALPHA * target + (1 - ALPHA) * ema_state
                payload_data = ema_state.astype(np.uint8)
                
                # Transmit
                payload = bytearray([255]) + bytearray(payload_data.tolist())
                ser.write(payload)

except KeyboardInterrupt:
    print("\n\nOverride dormant. Disconnecting.")
    ser.write(bytearray([255]) + bytearray([0]*15))
    ser.close()