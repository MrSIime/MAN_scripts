import numpy as np
from PIL import Image
import random
import os

def decode(image_path: str, output_path: str, key: int) -> None:
    if not os.path.exists(image_path):
        return

    px = np.array(Image.open(image_path).convert("RGB"), dtype=np.uint8)
    
    flat = px.reshape(-1)
    indices = list(range(len(flat)))
    
    # Відновлюємо той самий порядок перемішування за ключем
    random.Random(key).shuffle(indices)

    extracted = []
    
    # 1. Читаємо довжину (перші 32 біти у перемішаному порядку)
    for i in range(32):
        extracted.append(str(flat[indices[i]] & 1))

    length = int("".join(extracted), 2)
    total_bits = 32 + (length * 8)

    # 2. Читаємо решту (текст)
    for i in range(32, total_bits):
        extracted.append(str(flat[indices[i]] & 1))

    bits_str = "".join(extracted[32:])
    data = bytes(int(bits_str[i:i+8], 2) for i in range(0, len(bits_str), 8))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(data.decode("utf-8", errors="ignore"))