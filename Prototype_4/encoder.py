import numpy as np
from PIL import Image
import random
import os
import base64

def encode(image_path: str, text_path: str, output_path: str, user_key: int) -> None:
    if not os.path.exists(image_path) or not os.path.exists(text_path):
        raise FileNotFoundError("Files not found.")

    with open(text_path, "rb") as f:
        raw_data = bytearray(f.read())

    indices_text = list(range(len(raw_data)))
    random.Random(user_key).shuffle(indices_text)
    
    shuffled_data = bytearray(len(raw_data))
    for i, idx in enumerate(indices_text):
        shuffled_data[i] = raw_data[idx]

    if user_key % 2 == 0:
        encoded_data = base64.b64encode(shuffled_data)
    else:
        encoded_data = base64.b32encode(shuffled_data)

    payload = len(encoded_data).to_bytes(4, "big") + encoded_data
    bits = [int(b) for byte in payload for b in f"{byte:08b}"]

    if user_key % 3 == 0:
        bits = [1 - b for b in bits]

    img = Image.open(image_path).convert("RGB")
    px = np.array(img, dtype=np.uint8)
    
    r, g, b = px[-1, -1]
    auto_seed = int(f"{r:03d}{g:03d}{b:03d}")

    flat_px = px.reshape(-1)
    indices_px = list(range(flat_px.size - 3))

    if len(bits) > len(indices_px):
        raise ValueError("Image too small for this data.")

    random.Random(auto_seed).shuffle(indices_px)

    for i, bit in enumerate(bits):
        idx = indices_px[i]
        flat_px[idx] = (flat_px[idx] & 0xFE) | bit

    Image.fromarray(px).save(output_path)