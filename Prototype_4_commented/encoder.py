import numpy as np  # імпорт numpy для маніпуляцій з масивами пікселів
from PIL import Image  # імпорт Image для читання/запису зображень
import random  # імпорт random для детермінованого перемішування
import os  # імпорт os для перевірки існування файлів
import base64  # імпорт base64 для кодування/декодування байтів

def encode(image_path: str, text_path: str, output_path: str, user_key: int) -> None:  # головна функція кодування з додатковими опціями
    if not os.path.exists(image_path) or not os.path.exists(text_path):
        raise FileNotFoundError("Files not found.")  # перевіряє наявність обох файлів, інакше кидає помилку

    with open(text_path, "rb") as f:
        raw_data = bytearray(f.read())  # читає файл у бінарному режимі і приводить в mutable bytearray

    indices_text = list(range(len(raw_data)))  # створює список індексів для даних тексту
    random.Random(user_key).shuffle(indices_text)  # перемішує індекси детерміновано за ключем користувача
    
    shuffled_data = bytearray(len(raw_data))  # створює масив потрібної довжини для перемішаних байтів
    for i, idx in enumerate(indices_text):
        shuffled_data[i] = raw_data[idx]  # переставляє байти у відповідності до перемішаних індексів

    if user_key % 2 == 0:
        encoded_data = base64.b64encode(shuffled_data)  # якщо ключ парний — використовує base64
    else:
        encoded_data = base64.b32encode(shuffled_data)  # якщо ключ непарний — використовує base32

    payload = len(encoded_data).to_bytes(4, "big") + encoded_data  # формує payload: 4 байти довжини + закодовані дані
    bits = [int(b) for byte in payload for b in f"{byte:08b}"]  # перетворює кожен байт payload у список бітів

    if user_key % 3 == 0:
        bits = [1 - b for b in bits]  # якщо ключ кратний 3 — інвертує всі біти payload

    img = Image.open(image_path).convert("RGB")  # відкриває зображення і приводить до RGB
    px = np.array(img, dtype=np.uint8)  # конвертує зображення в numpy-масив байтів
    
    r, g, b = px[-1, -1]  # читає останній піксель (нижній правий) для автогенерації seed
    auto_seed = int(f"{r:03d}{g:03d}{b:03d}")  # формує числовий seed з трьох каналів останнього пікселя

    flat_px = px.reshape(-1)  # вирівнює масив пікселів у одну вимірність
    indices_px = list(range(flat_px.size - 3))  # створює список індексів, резервуючи останні 3 значення

    if len(bits) > len(indices_px):
        raise ValueError("Image too small for this data.")  # перевірка, чи вистачає місця для всіх бітів

    random.Random(auto_seed).shuffle(indices_px)  # перемішує індекси пікселів на основі автогенерованого seed

    for i, bit in enumerate(bits):
        idx = indices_px[i]
        flat_px[idx] = (flat_px[idx] & 0xFE) | bit  # записує біт у молодший біт вибраного елементу масиву

    Image.fromarray(px).save(output_path)  # зберігає змінене зображення у вказаний шлях
