import numpy as np
from PIL import Image

def encode(image_path: str, text_path: str, output_path: str) -> None:
    
    def text_to_bits(text_bytes: bytes) -> str:
        bits = "".join(f"{b:08b}" for b in text_bytes)
        return bits

    try:
        img = Image.open(image_path).convert("RGB")
    except FileNotFoundError:
        return

    try:
        with open(text_path, "r", encoding="utf-8") as f:
            text_bytes = f.read().encode("utf-8")
    except FileNotFoundError:
        return

    length_bytes = len(text_bytes).to_bytes(4, "big")
    full_data = length_bytes + text_bytes
    
    bits_to_hide = text_to_bits(full_data)
    total_bits_count = len(bits_to_hide)

    px = np.array(img, dtype=np.uint8)
    
    flat_px = px.flatten()
    
    if total_bits_count > len(flat_px):
        return

    
    for i in range(total_bits_count):
        bit = int(bits_to_hide[i])
        flat_px[i] = (flat_px[i] & 254) | bit

    new_px = flat_px.reshape(px.shape)
    img_out = Image.fromarray(new_px, "RGB")
    
    img_out.save(output_path)
    