import numpy as np
from PIL import Image
import random
import os

def encode(image_path: str, text_path: str, output_path: str, key: int) -> None:
    if not os.path.exists(image_path) or not os.path.exists(text_path):
        return

    img = Image.open(image_path).convert("RGB")
    px = np.array(img, dtype=np.uint8)
    h, w, c = px.shape

    with open(text_path, "r", encoding="utf-8") as f:
        data = f.read().encode("utf-8")

    length_bytes = len(data).to_bytes(4, "big")
    bits = "".join(f"{b:08b}" for b in length_bytes + data)

    flat = px.reshape(-1)
    indices = list(range(len(flat)))

    if len(bits) > len(indices):
        return

    random.Random(key).shuffle(indices)

    for i, b in enumerate(bits):
        idx = indices[i]
        flat[idx] = (flat[idx] & 254) | int(b)

    Image.fromarray(flat.reshape(h, w, c), "RGB").save(output_path)