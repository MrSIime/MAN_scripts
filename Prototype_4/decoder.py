import numpy as np
from PIL import Image
import random
import os
import base64

def decode(image_path: str, output_path: str, user_key: int) -> None:
    if not os.path.exists(image_path):
        raise FileNotFoundError("Image not found.")

    img = Image.open(image_path).convert("RGB")
    px = np.array(img, dtype=np.uint8)

    r, g, b = px[-1, -1]
    auto_seed = int(f"{r:03d}{g:03d}{b:03d}")

    flat_px = px.reshape(-1)
    indices_px = list(range(flat_px.size - 3))
    random.Random(auto_seed).shuffle(indices_px)

    def get_bits(count, start_offset=0):
        extracted = []
        for i in range(start_offset, start_offset + count):
            if i < len(indices_px):
                bit = flat_px[indices_px[i]] & 1
                extracted.append(bit)
        
        if user_key % 3 == 0:
            extracted = [1 - b for b in extracted]
        return extracted

    len_bits = get_bits(32, start_offset=0)
    len_str = "".join(map(str, len_bits))
    data_length = int(len_str, 2)

    payload_bits = get_bits(data_length * 8, start_offset=32)
    payload_str = "".join(map(str, payload_bits))
    
    encoded_data = bytes(int(payload_str[i:i+8], 2) for i in range(0, len(payload_str), 8))

    try:
        if user_key % 2 == 0:
            shuffled_data = base64.b64decode(encoded_data)
        else:
            shuffled_data = base64.b32decode(encoded_data)
    except Exception:
        raise ValueError("Decoding failed. Wrong Key or Data corrupted.")

    original_data = bytearray(len(shuffled_data))
    indices_text = list(range(len(shuffled_data)))
    random.Random(user_key).shuffle(indices_text)

    for i, original_idx in enumerate(indices_text):
        original_data[original_idx] = shuffled_data[i]

    with open(output_path, "wb") as f:
        f.write(original_data)