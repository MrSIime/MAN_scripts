import os
import ecoder
import Prototype_1.decoder as decoder

def main():
    print("=== Steganography Tool (LSB + Seed) ===")
    print("1. Сховати текст в картинку")
    print("2. Дістати текст з картинки")
    print("0. Вихід")
    
    choice = input("Ваш вибір: ").strip()

    if choice == "1":
        img_path = input("Шлях до картинки (наприклад, image.png): ").strip()
        txt_path = input("Шлях до тексту (наприклад, text.txt): ").strip()
        out_path = input("Назва вихідного файлу (наприклад, secret.png): ").strip()
        
        if not out_path: 
            out_path = "secret_image.png"
            
        try:
            seed = int(input("Придумайте цифровий ключ (seed): "))
            ecoder.encode(img_path, txt_path, out_path, seed)
        except ValueError:
            print("[Помилка] Ключ має бути цілим числом.")

    elif choice == "2":
        img_path = input("Шлях до картинки з секретом: ").strip()
        out_txt = input("Куди зберегти текст (наприклад, decoded.txt): ").strip()
        
        if not out_txt:
            out_txt = "decoded_text.txt"
            
        try:
            seed = int(input("Введіть ключ (seed), яким шифрували: "))
            decoder.decode(img_path, out_txt, seed)
        except ValueError:
            print("[Помилка] Ключ має бути цілим числом.")
            
    elif choice == "0":
        print("До побачення!")
    else:
        print("Невірний вибір.")

if __name__ == "__main__":
    main()