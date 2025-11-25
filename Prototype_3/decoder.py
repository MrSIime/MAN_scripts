import numpy as np
from PIL import Image
import random

def decode(image_path: str, output_text_path: str, manual_seed: int) -> None:
    
    def bits_to_bytes(bits: str) -> bytes:
        return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))

    def unshuffle_bytes(data: bytes, key_bytes: bytes) -> bytes:
        rng = random.Random(int.from_bytes(key_bytes, "big"))
        idx = list(range(len(data)))
        rng.shuffle(idx)
        original = bytearray(len(data))
        for new_pos, old_pos in enumerate(idx):
            original[old_pos] = data[new_pos]
        return bytes(original)
        
    def xor_bytes(data: bytes, key_bytes: bytes) -> bytes:
        return bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data)])

    try:
        img = Image.open(image_path).convert("RGB")
    except FileNotFoundError:
        print(f"[Помилка] Файл зображення '{image_path}' не знайдено.")
        return

    print("Зчитування пікселів...")
    px = np.array(img, dtype=np.uint8)
    flat = px.reshape(-1, 3)

    extracted_bits = []

    extracted_bits_str = "".join([str(val % 2) for val in flat.flatten()])

    len_bits = extracted_bits_str[:32]
    length_bytes = bits_to_bytes(len_bits)
    text_length = int.from_bytes(length_bytes, "big")

    if text_length <= 0 or text_length * 8 > len(extracted_bits_str) - 32:
        print("[Помилка] Не вдалося коректно прочитати довжину даних. Можливо, неправильний файл або він порожній.")
        return

    print(f"Виявлено приховані дані розміром {text_length} байт.")

    start = 32
    end = start + (text_length * 8)
    data_bits = extracted_bits_str[start:end]
    encrypted_data = bits_to_bytes(data_bits)

    key_bytes = (manual_seed % (2**32)).to_bytes(4, "big")

    try:
        decrypted_xor = xor_bytes(encrypted_data, key_bytes)
        original_data = unshuffle_bytes(decrypted_xor, key_bytes)
        
        with open(output_text_path, "w", encoding="utf-8") as f:
            f.write(original_data.decode("utf-8"))
        print(f"[Успіх] Текст збережено у файл '{output_text_path}'.")
        
    except UnicodeDecodeError:
        print("[Помилка] Текст розшифровано некоректно. Ви ввели правильний seed?")
    except Exception as e:
        print(f"[Помилка] {e}")