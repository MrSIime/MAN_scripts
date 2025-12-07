import numpy as np  # імпорт numpy
from PIL import Image  # імпорт Image з Pillow
import random  # імпорт random для детермінованого перемішування індексів
import os  # імпорт os для перевірки файлу

def decode(image_path: str, output_path: str) -> None:  # функція для витягування тексту зі зображення
    if not os.path.exists(image_path):
        return  # якщо файл не знайдено — вихід
        
    px = np.array(Image.open(image_path).convert("RGB"), dtype=np.uint8)  # читає зображення і отримує numpy-масив
    
    r, g, b = px[-1, -1]  # читає останній піксель, з якого формувався seed під час кодування
    seed_str = f"{r:03d}{g:03d}{b:03d}"  # формує той самий рядок seed
    seed = int(seed_str)  # перетворює seed у число
    
    flat = px.reshape(-1)  # вирівнює масив у 1D
    indices = list(range(len(flat) - 3))  # створює список індексів, резервуючи останні 3 елементи
    random.Random(seed).shuffle(indices)  # переставляє індекси тим же seed
    
    extracted = []  # список для збереження бітів

    for i in range(32):
        extracted.append(str(flat[indices[i]] & 1))  # читає перші 32 біти (заголовок довжини)
    
    length = int("".join(extracted), 2)  # об'єднує 32 біти в число — довжина тексту у байтах
    total_bits = 32 + (length * 8)  # загальна кількість біт для читання
    
    for i in range(32, total_bits):
        extracted.append(str(flat[indices[i]] & 1))  # читає біти, що містять текст
        
    bits_str = "".join(extracted[32:])  # формує біт-рядок тексту без заголовка
    data = bytes(int(bits_str[i:i+8], 2) for i in range(0, len(bits_str), 8))  # перетворює біт-рядок на байти
    
    with open(output_path, "w", encoding="utf-8") as f:  # відкриває файл для запису результуючого тексту
        f.write(data.decode("utf-8", errors="ignore"))  # декодує байти в текст і записує (ігнорує помилки декодування)
