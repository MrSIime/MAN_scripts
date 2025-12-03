import encoder
import decoder
import sys

def main():
    print("=== GEN4 Steganography (Dual Key + Base64/32 + Inversion) ===")
    mode = input("[1] Encode\n[2] Decode\n>>> ").strip()

    try:
        if mode == "1":
            img = input("Image path: ").strip()
            txt = input("Text path: ").strip()
            out = input("Output image: ").strip()
            key = int(input("User Numeric Key: ").strip())
            
            encoder.encode(img, txt, out, key)
            print("Done. Don't forget your User Key!")

        elif mode == "2":
            img = input("Image path: ").strip()
            out = input("Output text file: ").strip()
            key = int(input("Enter User Numeric Key: ").strip())

            decoder.decode(img, out, key)
            print("Done.")

    except Exception as e:
        print(f"[Error] {e}")

if __name__ == "__main__":
    main()