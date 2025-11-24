import numpy as np
from PIL import Image
import os, random
import math

def coder(image_path: str, text_path: str, output_path: str) -> None:
    def enforce_parity(value: int, target_parity: int) -> int:
        if value % 2 == target_parity:
            return value
        else:
            if target_parity == 0:
                return value - 1 if value > 0 else 0
            else:
                return value + 1 if value < 255 else 255

    def apply_bitstring_to_pixels(pixels: np.ndarray, bitstring: str) -> np.ndarray:
        h, w, _ = pixels.shape
        flat = pixels.reshape(-1, 3).copy()
        for i, b in enumerate(bitstring):
            pix_idx, ch_idx = divmod(i, 3)
            flat[pix_idx, ch_idx] = enforce_parity(flat[pix_idx, ch_idx], int(b))
        return flat.reshape(h, w, 3)

    def read_text(path: str) -> bytes:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().encode("utf-8")

    def bytes_to_bits(data: bytes) -> str:
        return "".join(f"{b:08b}" for b in data)

    def shuffle_bytes(data: bytes, key_bytes: bytes) -> bytes:
        rng = random.Random(int.from_bytes(key_bytes, "big"))
        idx = list(range(len(data)))
        rng.shuffle(idx)
        shuffled = bytearray(len(data))
        for new_pos, old_pos in enumerate(idx):
            shuffled[new_pos] = data[old_pos]
        return bytes(shuffled)

    def xor_bytes(data: bytes, key_bytes: bytes) -> bytes:
        return bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data)])

    try:
        img = Image.open(image_path).convert("RGB")
    except FileNotFoundError:
        print(f"Error: The image file '{image_path}' was not found.")
        return

    px = np.array(img, dtype=np.uint8)
    w, h = img.size
    total_capacity_bits = w * h * 3

    data_bytes = read_text(text_path)
    key_bytes = os.urandom(4)
    shuffled = shuffle_bytes(data_bytes, key_bytes)
    encrypted = xor_bytes(shuffled, key_bytes)

    length_bytes = len(data_bytes).to_bytes(4, "big")
    header_bytes = key_bytes + length_bytes
    total_bits_to_hide = len(bytes_to_bits(header_bytes)) + len(bytes_to_bits(encrypted))

    if total_capacity_bits >= total_bits_to_hide:
        total_bits_string = bytes_to_bits(header_bytes) + bytes_to_bits(encrypted)
        new_px = apply_bitstring_to_pixels(px, total_bits_string)
        Image.fromarray(new_px, "RGB").save(output_path)
        print("Data embedded successfully.")
        print(f"Key (hex): {key_bytes.hex()}")
    else:
        print("Data is too large to embed in this image.")
        bits_needed = total_bits_to_hide - total_capacity_bits
        print(f"Missing capacity: {bits_needed} bits.")
        
        current_pixels = w * h
        pixels_needed = math.ceil(total_bits_to_hide / 3)
        
        scale_factor = (pixels_needed / current_pixels)**0.5
        scale_percentage = (scale_factor - 1) * 100
        
        print(f"To embed the data, the image needs to be scaled up by at least {scale_percentage:.2f}%.")
        
        user_choice = input("Would you like to automatically resize the image and proceed? (y/n): ").lower()
        if user_choice == 'y':
            new_w = math.ceil(w * scale_factor)
            new_h = math.ceil(h * scale_factor)
            print(f"Resizing image to {new_w}x{new_h}...")
            resized_img = img.resize((new_w, new_h))
            resized_px = np.array(resized_img, dtype=np.uint8)
            
            total_bits_string = bytes_to_bits(header_bytes) + bytes_to_bits(encrypted)
            new_px = apply_bitstring_to_pixels(resized_px, total_bits_string)
            Image.fromarray(new_px, "RGB").save(output_path)
            print("Data embedded successfully into the resized image.")
            print(f"Key (hex): {key_bytes.hex()}")
        else:
            print("Operation aborted by user. No changes were made.")