import numpy as np
from PIL import Image
import random
import os

def decode(image_path: str, output_path: str) -> None:
    if not os.path.exists(image_path):
        return
        
    px = np.array(Image.open(image_path).convert("RGB"), dtype=np.uint8)
    
    r, g, b = px[-1, -1]
    seed_str = f"{r:03d}{g:03d}{b:03d}"
    seed = int(seed_str)
    
    flat = px.reshape(-1)
    indices = list(range(len(flat) - 3))
    random.Random(seed).shuffle(indices)
    
    extracted = []

    for i in range(32):
        extracted.append(str(flat[indices[i]] & 1))
    
    length = int("".join(extracted), 2)
    total_bits = 32 + (length * 8)
    
    for i in range(32, total_bits):
        extracted.append(str(flat[indices[i]] & 1))
        
    bits_str = "".join(extracted[32:])
    data = bytes(int(bits_str[i:i+8], 2) for i in range(0, len(bits_str), 8))
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(data.decode("utf-8", errors="ignore"))