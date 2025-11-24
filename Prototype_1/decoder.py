import numpy as np
from PIL import Image
import random
import os

def decoder(image_path: str, output_path: str) -> None:
    def bits_to_bytes(bits: str) -> bytes:
        b = bytearray()
        for i in range(0, len(bits), 8):
            b.append(int(bits[i:i+8], 2))
        return bytes(b)

    def get_bits_from_pixels(px: np.ndarray, n_bits: int) -> str:
        flat = px.reshape(-1, 3)
        bits = []
        for pix in flat:
            for ch in pix:
                bits.append(str(ch % 2))
                if len(bits) >= n_bits:
                    return "".join(bits)
        return "".join(bits)

    def inverse_shuffle_bytes(data: bytes, key_bytes: bytes) -> bytes:
        rng = random.Random(int.from_bytes(key_bytes, "big"))
        idx = list(range(len(data)))
        rng.shuffle(idx)
        original = bytearray(len(data))
        for new_pos, old_pos in enumerate(idx):
            original[old_pos] = data[new_pos]
        return bytes(original)

    def xor_bytes(data: bytes, key_bytes: bytes) -> bytes:
        return bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data)])

    img = Image.open(image_path).convert("RGB")
    px = np.array(img, dtype=np.uint8)

    header_bits = get_bits_from_pixels(px, 64)
    header_bytes = bits_to_bytes(header_bits)
    key_bytes = header_bytes[:4]
    data_len = int.from_bytes(header_bytes[4:], "big")

    data_bits_len = data_len * 8
    all_bits = get_bits_from_pixels(px, 64 + data_bits_len)
    encrypted_bits = all_bits[64:64 + data_bits_len]
    encrypted_bytes = bits_to_bytes(encrypted_bits)

    shuffled_bytes = xor_bytes(encrypted_bytes, key_bytes)
    original_bytes = inverse_shuffle_bytes(shuffled_bytes, key_bytes)
    
    recovered_text = original_bytes.decode("utf-8")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(recovered_text)

    print(f"Recovered text saved to {output_path}")