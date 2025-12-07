import numpy as np  # імпортує бібліотеку numpy під псевдонімом np для роботи з масивами
from PIL import Image  # імпортує клас Image з пакету Pillow для роботи з зображеннями

def encode(image_path: str, text_path: str, output_path: str) -> None:  # функція кодування тексту в зображення
    
    def text_to_bits(text_bytes: bytes) -> str:  # внутрішня допоміжна функція: перетворює байти в рядок бітів
        bits = "".join(f"{b:08b}" for b in text_bytes)  # для кожного байта створює 8-бітний бінарний рядок і з'єднує їх
        return bits  # повертає згенерований рядок бітів

    try:
        img = Image.open(image_path).convert("RGB")  # відкриває зображення і конвертує в RGB формат
    except FileNotFoundError:
        return  # якщо файл зображення не знайдено — виходимо з функції

    try:
        with open(text_path, "r", encoding="utf-8") as f:  # відкриває текстовий файл у режимі читання з кодуванням UTF-8
            text_bytes = f.read().encode("utf-8")  # читає текст і конвертує в байти UTF-8
    except FileNotFoundError:
        return  # якщо текстовий файл не знайдено — виходимо

    length_bytes = len(text_bytes).to_bytes(4, "big")  # обчислює довжину тексту та упаковує її у 4 байти (Big-endian)
    full_data = length_bytes + text_bytes  # створює повний масив даних: заголовок (довжина) + сам текст
    
    bits_to_hide = text_to_bits(full_data)  # перетворює весь пакет байтів у послідовність бітів
    total_bits_count = len(bits_to_hide)  # підраховує загальну кількість бітів для вбудовування

    px = np.array(img, dtype=np.uint8)  # перетворює зображення в numpy-масив типу unsigned byte
    
    flat_px = px.flatten()  # вирівнює (спрямовує) багатовимірний масив у 1D масив
    
    if total_bits_count > len(flat_px):
        return  # якщо бітів більше, ніж доступних елементів у пікселях — виходимо

    
    for i in range(total_bits_count):  # ітеруємо по кожному біту для вбудовування
        bit = int(bits_to_hide[i])  # перетворює символ '0'/'1' у ціле 0 або 1
        flat_px[i] = (flat_px[i] & 254) | bit  # очищає молодший біт пікселя і встановлює його в потрібне значення

    new_px = flat_px.reshape(px.shape)  # повертає масив до первісної форми зображення
    img_out = Image.fromarray(new_px, "RGB")  # створює об'єкт Image з зміненого масиву
    
    img_out.save(output_path)  # зберігає результуюче зображення у вказаний шлях
