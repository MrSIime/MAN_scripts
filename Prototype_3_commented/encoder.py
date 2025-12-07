import numpy as np  # імпорт numpy для роботи з масивами
from PIL import Image  # імпорт Pillow Image для роботи із зображеннями
import random  # імпорт random для детермінованого перемішування індексів
import os  # імпорт os для перевірки наявності файлів

def encode(image_path: str, text_path: str, output_path: str) -> None:  # функція кодування, яка використовує авто-генерацію seed з пікселя
    if not os.path.exists(image_path) or not os.path.exists(text_path):
        return  # якщо якесь з файлів відсутнє — виходимо
    
    img = Image.open(image_path).convert("RGB")  # відкриває зображення і конвертує в RGB
    px = np.array(img, dtype=np.uint8)  # перетворює зображення в numpy-масив байтів
    h, w, c = px.shape  # отримує розміри (висота, ширина, канали)
    
    r, g, b = px[-1, -1]  # читає значення останнього пікселя (нижній правий) — використовується як джерело часу
    
    seed_str = f"{r:03d}{g:03d}{b:03d}"  # формує рядок seed з трьох каналів, кожен у форматі 3 цифр
    seed = int(seed_str)  # перетворює рядок у ціле число seed
    
    with open(text_path, "r", encoding="utf-8") as f:
        data = f.read().encode("utf-8")  # читає текст і кодує у байти UTF-8
        
    length_bytes = len(data).to_bytes(4, "big")  # упаковує довжину тексту у 4 байти
    bits = "".join(f"{b:08b}" for b in length_bytes + data)  # формує бітову послідовність з довжини+даних
    
    flat = px.reshape(-1)  # вирівнює масив у 1D
    indices = list(range(len(flat) - 3))  # створює список індексів, резервуючи останні 3 елементи (для seed)
    
    if len(bits) > len(indices):
        return  # якщо недостатньо місця — вихід
        
    random.Random(seed).shuffle(indices)  # перемішує індекси на основі згенерованого seed
    
    for i, b in enumerate(bits):
        idx = indices[i]
        flat[idx] = (flat[idx] & 254) | int(b)  # вбудовує біт у молодший біт відповідного елементу
        
    Image.fromarray(flat.reshape(h, w, c), "RGB").save(output_path)  # збирає масив назад у зображення і зберігає
