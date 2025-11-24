import numpy as np
from PIL import Image

def encode(image_path: str, text_path: str, output_path: str) -> None:
    
    # --- Допоміжні функції ---
    def text_to_bits(text_bytes: bytes) -> str:
        # Перетворюємо байти в рядок бітів (010101...)
        bits = "".join(f"{b:08b}" for b in text_bytes)
        return bits

    # --- Основна логіка ---
    try:
        img = Image.open(image_path).convert("RGB")
    except FileNotFoundError:
        print(f"[Помилка] Картинку '{image_path}' не знайдено.")
        return

    try:
        with open(text_path, "r", encoding="utf-8") as f:
            text_bytes = f.read().encode("utf-8")
    except FileNotFoundError:
        print(f"[Помилка] Текстовий файл '{text_path}' не знайдено.")
        return

    # 1. Формуємо дані: [4 байти довжини] + [Текст]
    # Це потрібно, щоб декодер знав, де зупинитися
    length_bytes = len(text_bytes).to_bytes(4, "big")
    full_data = length_bytes + text_bytes
    
    bits_to_hide = text_to_bits(full_data)
    total_bits_count = len(bits_to_hide)

    px = np.array(img, dtype=np.uint8)
    
    # Робимо плаский масив (одна довга стрічка значень R, G, B, R, G, B...)
    flat_px = px.flatten()
    
    # Перевірка місткості
    if total_bits_count > len(flat_px):
        print(f"[Помилка] Картинка замала! Потрібно пікселів (каналів): {total_bits_count}, є: {len(flat_px)}")
        return

    print("Запис даних піксель за пікселем...")

    # 2. Записуємо біти підряд
    # Використовуємо бітові операції:
    # (val & 254) -> обнуляє останній біт (робить число парним)
    # | int(bit)  -> додає наш біт (0 або 1)
    
    for i in range(total_bits_count):
        bit = int(bits_to_hide[i])
        flat_px[i] = (flat_px[i] & 254) | bit

    # 3. Відновлюємо форму картинки і зберігаємо
    new_px = flat_px.reshape(px.shape)
    img_out = Image.fromarray(new_px, "RGB")
    
    img_out.save(output_path)
    print(f"[Успіх] Текст записано у файл '{output_path}'.")