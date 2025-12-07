import numpy as np  # імпорт numpy для роботи з масивами
from PIL import Image  # імпорт Image для обробки зображень
import random  # імпорт random для детермінованого перемішування індексів
import os  # імпорт os для перевірки існування файлів

def encode(image_path: str, text_path: str, output_path: str, key: int) -> None:  # функція кодування з використанням ключа
    if not os.path.exists(image_path) or not os.path.exists(text_path):
        return  # якщо файл зображення або тексту відсутні — вихід

    img = Image.open(image_path).convert("RGB")  # відкриває зображення і конвертує в RGB
    px = np.array(img, dtype=np.uint8)  # створює numpy-масив з даних зображення
    h, w, c = px.shape  # зчитує висоту, ширину і кількість каналів

    with open(text_path, "r", encoding="utf-8") as f:
        data = f.read().encode("utf-8")  # читає текстовий файл і кодує у байти UTF-8

    # Формуємо біти: [4 байти довжини] + [текст]
    length_bytes = len(data).to_bytes(4, "big")  # упаковує довжину тексту у 4 байти
    bits = "".join(f"{b:08b}" for b in length_bytes + data)  # створює бітову послідовність для всіх байтів

    flat = px.reshape(-1)  # вирівнює масив у 1D послідовність
    indices = list(range(len(flat)))  # створює список індексів для всіх елементів масиву

    if len(bits) > len(indices):
        return  # якщо бітів більше, ніж доступних елементів — вихід

    # Перемішуємо індекси на основі введеного ключа
    random.Random(key).shuffle(indices)  # створює генератор з фіксованим seed і переставляє індекси

    for i, b in enumerate(bits):  # для кожного біта знаходимо відповідний елемент масиву через перемішані індекси
        idx = indices[i]
        flat[idx] = (flat[idx] & 254) | int(b)  # записуємо біт у молодший біт відповідного елементу

    Image.fromarray(flat.reshape(h, w, c), "RGB").save(output_path)  # збираємо масив назад у зображення і зберігаємо
