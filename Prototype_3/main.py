import encoder
import decoder

def main():
    mode = input().strip()
    
    if mode == "1":
        img = input().strip()
        txt = input().strip()
        out = input().strip()
        try:
            encoder.encode(img, txt, out)
        except:
            pass
            
    elif mode == "2":
        img = input().strip()
        out = input().strip()
        try:
            decoder.decode(img, out)
        except:
            pass

if __name__ == "__main__":
    main()