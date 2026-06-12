import numpy as np
import serial
import time
import sys

# System Port Configuration (Update 'COM6' or '/dev/ttyUSB0' as needed)
PORT = 'COM6' 
BAUD_RATE = 115200

try:
    ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
    time.sleep(2) 
except Exception as e:
    print(f"HARDWARE FAULT: Could not connect to {PORT}. {e}")
    sys.exit(1)

# ---------------------------------------------------------
# NEURAL CALIBRATION: Expanded Latent Space & Amplified Variance
# ---------------------------------------------------------
np.random.seed(42)

# Input dimension: 2 (sin and cos for orbital time evolution)
# Latent dimension: 4
# Output dimension: 18
W1 = np.random.randn(2, 4) * 3.0  
b1 = np.random.randn(4) * 0.5     

W2 = np.random.randn(4, 18) * 3.0 
b2 = np.random.randn(18) * 0.5    

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

ema_state = np.zeros(18)
ALPHA = 0.03 # Extreme smoothing coefficient for 60fps capture

print("Initiating Calibrated MechNeuron Matrix. Press Ctrl+C to terminate.")
t = 0.0

try:
    while True:
        # 1. Forward Pass (Orbital Time Input)
        # Using the golden ratio (0.618) to offset frequency and avoid looping repetition
        input_node = np.array([[np.sin(t), np.cos(t * 0.618)]]) 
        
        # Layer 1
        latent = sigmoid(np.dot(input_node, W1) + b1)
        
        # Layer 2
        output = sigmoid(np.dot(latent, W2) + b2)[0] 
        
        # 2. Dynamic Range Expansion (Force extreme contrast)
        out_min = np.min(output)
        out_max = np.max(output)
        if out_max > out_min:
            normalized_output = (output - out_min) / (out_max - out_min)
        else:
            normalized_output = output
            
        target = normalized_output * 254
        
        # 3. Apply EMA for cinematic fluidity
        ema_state = ALPHA * target + (1 - ALPHA) * ema_state
        payload_data = ema_state.astype(np.uint8)
        
        # 4. Packet Framing & Payload Construction
        payload = bytearray([255]) + bytearray(payload_data.tolist())
        
        # 5. Transmit & Await Acknowledgment 
        ser.write(payload)
        ack = ser.read(1)
        
        t += 0.015 # Network evolution rate

except KeyboardInterrupt:
    print("\nMatrix dormant. Disconnecting.")
    off_payload = bytearray([255]) + bytearray([0]*18)
    ser.write(off_payload)
    ser.close()