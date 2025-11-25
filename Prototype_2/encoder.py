import numpy as np
from PIL import Image
import random

def encode(image_path: str, text_path: str, output_path: str, manual_seed: int) -> None:

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

    def bytes_to_bits(data: bytes) -> str:
        return "".join(f"{b:08b}" for b in data)

    try:
        img = Image.open(image_path).convert("RGB")
    except FileNotFoundError:
        print(f"[Помилка] Файл зображення '{image_path}' не знайдено.")
        return

    try:
        with open(text_path, "r", encoding="utf-8") as f:
            data_bytes = f.read().encode("utf-8")
    except FileNotFoundError:
        print(f"[Помилка] Текстовий файл '{text_path}' не знайдено.")
        return

    px = np.array(img, dtype=np.uint8)
    w, h = img.size
    total_capacity_bits = w * h * 3

    key_bytes = (manual_seed % (2**32)).to_bytes(4, "big")

    shuffled = shuffle_bytes(data_bytes, key_bytes)
    encrypted = xor_bytes(shuffled, key_bytes)

    length_bytes = len(data_bytes).to_bytes(4, "big")
    
    total_bits_string = bytes_to_bits(length_bytes) + bytes_to_bits(encrypted)

    if total_capacity_bits >= len(total_bits_string):
        print("Процес вбудовування розпочато...")
        new_px = apply_bitstring_to_pixels(px, total_bits_string)
        Image.fromarray(new_px, "RGB").save(output_path)
        print(f"[Успіх] Дані приховано в '{output_path}'.")
        print(f"Запам'ятайте ключ (seed): {manual_seed}")
    else:
        print("[Помилка] Текст занадто великий для цього зображення.")