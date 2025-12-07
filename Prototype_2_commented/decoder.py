import numpy as np  # імпорт numpy
from PIL import Image  # імпорт Pillow Image
import random  # імпорт random для детермінованого перемішування індексів
import os  # імпорт os для перевірки наявності файлу

def decode(image_path: str, output_path: str, key: int) -> None:  # функція декодування з використанням ключа
    if not os.path.exists(image_path):
        return  # якщо зображення не знайдено — виходимо

    px = np.array(Image.open(image_path).convert("RGB"), dtype=np.uint8)  # читає зображення і конвертує в numpy-масив
    
    flat = px.reshape(-1)  # вирівнює масив у 1D
    indices = list(range(len(flat)))  # створює список індексів для всіх елементів
    
    # Відновлюємо той самий порядок перемішування за ключем
    random.Random(key).shuffle(indices)  # переставляє індекси тим самим ключем

    extracted = []  # список для збереження витягнутих бітів
    
    # 1. Читаємо довжину (перші 32 біти у перемішаному порядку)
    for i in range(32):
        extracted.append(str(flat[indices[i]] & 1))  # читаємо молодший біт кожного елементу за перемішаним індексом

    length = int("".join(extracted), 2)  # об'єднуємо перші 32 біти в рядок і конвертуємо у число — довжина в байтах
    total_bits = 32 + (length * 8)  # загальна кількість бітів, що потрібно прочитати (заголовок + текст)

    # 2. Читаємо решту (текст)
    for i in range(32, total_bits):
        extracted.append(str(flat[indices[i]] & 1))  # продовжуємо читати біти у тому ж перемішаному порядку

    bits_str = "".join(extracted[32:])  # формуємо рядок бітів, що представляє текст (без заголовка)
    data = bytes(int(bits_str[i:i+8], 2) for i in range(0, len(bits_str), 8))  # групуємо по 8 біт і перетворюємо у байти

    with open(output_path, "w", encoding="utf-8") as f:  # відкриває файл в режимі запису UTF-8
        f.write(data.decode("utf-8", errors="ignore"))  # декодує байти в текст і записує у файл (ігнорує помилки)
