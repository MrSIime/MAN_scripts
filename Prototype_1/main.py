import encoder  # Тепер імпортуємо encoder, а не ecoder
import decoder
import os

def main():
    print("=== Sequential Steganography (Simple LSB) ===")
    print("Цей метод записує дані підряд без пароля.")
    print("1. Сховати текст")
    print("2. Дістати текст")
    print("0. Вихід")
    
    choice = input("Ваш вибір: ").strip()

    if choice == "1":
        img_path = input("Шлях до картинки (наприклад, image.png): ").strip()
        txt_path = input("Шлях до тексту (наприклад, text.txt): ").strip()
        out_path = input("Назва нової картинки (наприклад, secret.png): ").strip()
        
        # Якщо користувач просто натиснув Enter, даємо стандартну назву
        if not out_path: 
            out_path = "secret_lsb.png"
        
        # Викликаємо функцію з encoder.py
        try:
            encoder.encode(img_path, txt_path, out_path)
        except AttributeError:
             print("[Помилка] Перевірте, чи правильно названо функцію всередині encoder.py (має бути def encode...)")
        except Exception as e:
            print(f"[Помилка] {e}")

    elif choice == "2":
        img_path = input("Шлях до картинки з секретом: ").strip()
        out_txt = input("Куди зберегти текст: ").strip()
        
        if not out_txt: 
            out_txt = "decoded_simple.txt"
        
        # Викликаємо функцію з decoder.py
        try:
            decoder.decode(img_path, out_txt)
        except Exception as e:
            print(f"[Помилка] {e}")

    elif choice == "0":
        print("Бувай!")
    else:
        print("Невірний вибір.")

if __name__ == "__main__":
    main()