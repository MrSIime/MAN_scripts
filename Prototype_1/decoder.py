import numpy as np
from PIL import Image

def decode(image_path: str, output_text_path: str) -> None:
    
    # --- Допоміжна функція ---
    def bits_to_bytes(bits: str) -> bytes:
        return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))

    # --- Основна логіка ---
    try:
        img = Image.open(image_path).convert("RGB")
    except FileNotFoundError:
        print(f"[Помилка] Картинку '{image_path}' не знайдено.")
        return

    print("Зчитування даних...")
    
    px = np.array(img, dtype=np.uint8)
    flat_px = px.flatten()

    # 1. Витягуємо всі молодші біти (LSB)
    # Це створює довгий рядок з 0 і 1 з усіх пікселів підряд
    # (val & 1) -> повертає 1, якщо число непарне, і 0, якщо парне
    extracted_bits_str = "".join(str(val & 1) for val in flat_px)

    # 2. Читаємо заголовок (перші 32 біти = 4 байти)
    header_bits = extracted_bits_str[:32]
    length_bytes = bits_to_bytes(header_bits)
    text_length = int.from_bytes(length_bytes, "big")

    print(f"Знайдена довжина тексту: {text_length} байт")

    # Перевірка на адекватність
    if text_length <= 0 or (text_length * 8) + 32 > len(extracted_bits_str):
        print("[Помилка] Некоректна довжина даних. Можливо, файл пошкоджено або в ньому немає прихованого тексту.")
        return

    # 3. Читаємо сам текст
    start = 32
    end = 32 + (text_length * 8)
    text_bits = extracted_bits_str[start:end]
    
    text_bytes = bits_to_bytes(text_bits)

    try:
        decoded_text = text_bytes.decode("utf-8")
        with open(output_text_path, "w", encoding="utf-8") as f:
            f.write(decoded_text)
        print(f"[Успіх] Текст збережено у '{output_text_path}'")
    except UnicodeDecodeError:
        print("[Помилка] Дані витягнуто, але це не схоже на текст (помилка кодування).")