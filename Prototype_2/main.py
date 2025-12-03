import encoder
import decoder

def main():
    mode = input("1-Encode, 2-Decode: ").strip()

    if mode == "1":
        img = input("Image path: ").strip()
        txt = input("Text path: ").strip()
        out = input("Output image path: ").strip()
        key = input("Enter secret numeric key: ").strip()
        
        try:
            encoder.encode(img, txt, out, int(key))
        except:
            pass

    elif mode == "2":
        img = input("Image path: ").strip()
        out = input("Output text path: ").strip()
        key = input("Enter secret numeric key: ").strip()
        
        try:
            decoder.decode(img, out, int(key))
        except:
            pass

if __name__ == "__main__":
    main()