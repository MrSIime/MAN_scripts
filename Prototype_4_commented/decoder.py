import numpy as np  # імпорт numpy для опрацювання масивів
from PIL import Image  # імпорт Image для роботи із зображеннями
import random  # імпорт random для детермінованого переставляння індексів
import os  # імпорт os для перевірки наявності файлу
import base64  # імпорт base64 для декодування даних

def decode(image_path: str, output_path: str, user_key: int) -> None:  # функція декодування, що використовує user_key
    if not os.path.exists(image_path):
        raise FileNotFoundError("Image not found.")  # якщо зображення відсутнє — кидає помилку

    img = Image.open(image_path).convert("RGB")  # відкриває зображення та конвертує в RGB
    px = np.array(img, dtype=np.uint8)  # перетворює зображення на numpy-масив байтів

    r, g, b = px[-1, -1]  # читає останній піксель, з якого формувався auto_seed при кодуванні
    auto_seed = int(f"{r:03d}{g:03d}{b:03d}")  # створює той самий числовий seed

    flat_px = px.reshape(-1)  # вирівнює масив пікселів у 1D
    indices_px = list(range(flat_px.size - 3))  # створює список індексів, резервуючи останні 3 елементи
    random.Random(auto_seed).shuffle(indices_px)  # перемішує індекси так само, як при кодуванні

    def get_bits(count, start_offset=0):  # допоміжна функція для витягування певної кількості біт з масиву
        extracted = []  # тимчасовий список для бітів
        for i in range(start_offset, start_offset + count):
            if i < len(indices_px):
                bit = flat_px[indices_px[i]] & 1  # читає молодший біт елементу за перемішаним індексом
                extracted.append(bit)  # додає біт до списку
        
        if user_key % 3 == 0:
            extracted = [1 - b for b in extracted]  # якщо ключ кратний 3 — інвертує біти назад
        return extracted  # повертає список отриманих бітів

    len_bits = get_bits(32, start_offset=0)  # витягує перші 32 біти, які містять довжину payload
    len_str = "".join(map(str, len_bits))  # перетворює список бітів у рядок '0101...'
    data_length = int(len_str, 2)  # інтерпретує цей рядок як двійкове число — довжина закодованих даних у байтах

    payload_bits = get_bits(data_length * 8, start_offset=32)  # витягує біти payload, починаючи з офсету 32
    payload_str = "".join(map(str, payload_bits))  # перетворює біти payload у рядок
    
    encoded_data = bytes(int(payload_str[i:i+8], 2) for i in range(0, len(payload_str), 8))  # групує по 8 біт у байти

    try:
        if user_key % 2 == 0:
            shuffled_data = base64.b64decode(encoded_data)  # якщо ключ парний — використовує base64 декод
        else:
            shuffled_data = base64.b32decode(encoded_data)  # якщо ключ непарний — використовує base32 декод
    except Exception:
        raise ValueError("Decoding failed. Wrong Key or Data corrupted.")  # якщо декодування не вдалось — кидаємо помилку

    original_data = bytearray(len(shuffled_data))  # створює mutable масив для відновлених байтів
    indices_text = list(range(len(shuffled_data)))  # індекси байтів для зворотнього переставляння
    random.Random(user_key).shuffle(indices_text)  # переставляє індекси тим самим user_key

    for i, original_idx in enumerate(indices_text):
        original_data[original_idx] = shuffled_data[i]  # відновлює порядок байтів у початковий вигляд

    with open(output_path, "wb") as f:  # відкриває файл для бінарного запису
        f.write(original_data)  # записує відновлені байти у файл
