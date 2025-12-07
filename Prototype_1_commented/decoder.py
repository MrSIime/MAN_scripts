import numpy as np  # імпорт numpy для роботи з масивами
from PIL import Image  # імпорт Image для відкриття/обробки зображень

def decode(image_path: str, output_text_path: str) -> None:  # функція для витягування тексту зі зображення
    
    def bits_to_bytes(bits: str) -> bytes:  # допоміжна функція: перетворює рядок бітів у байти
        return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))  # групує по 8 біт і перетворює у байт

    try:
        img = Image.open(image_path).convert("RGB")  # відкриває зображення і приводить до RGB
    except FileNotFoundError:
        return  # якщо файл не знайдено — виходимо
    
    px = np.array(img, dtype=np.uint8)  # конвертує зображення в numpy-масив байтів
    flat_px = px.flatten()  # вирівнює масив у 1D послідовність

    extracted_bits_str = "".join(str(val & 1) for val in flat_px)  # читає молодший біт кожного елементу і формує рядок бітів

    header_bits = extracted_bits_str[:32]  # перші 32 біти — заголовок із довжиною повідомлення
    length_bytes = bits_to_bytes(header_bits)  # перетворює ці 32 біти на 4 байти довжини
    text_length = int.from_bytes(length_bytes, "big")  # інтерпретує 4 байти як цілочисельну довжину (Big-endian)

    if text_length <= 0 or (text_length * 8) + 32 > len(extracted_bits_str):
        return  # якщо довжина некоректна або виходить за межі — виходимо

    start = 32  # початок бітів тексту після заголовка
    end = 32 + (text_length * 8)  # кінець — залежить від довжини тексту у байтах помноженої на 8
    text_bits = extracted_bits_str[start:end]  # вирізаємо бітову частину, яка відповідає тексту
    
    text_bytes = bits_to_bytes(text_bits)  # перетворюємо біт-рядок у байти

    try:
        decoded_text = text_bytes.decode("utf-8")  # пробуємо декодувати байти в UTF-8 рядок
        with open(output_text_path, "w", encoding="utf-8") as f:  # відкриваємо файл для запису результату
            f.write(decoded_text)  # записуємо декодований текст у файл
    except UnicodeDecodeError:
        return  # якщо декодування не вдалось — виходимо
