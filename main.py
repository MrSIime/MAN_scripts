import os
import coder
import decoder

def main():
    while True:
        print("\n--- Steganography Tool ---")
        print("1. Encode a file into an image")
        print("2. Decode a file from an image")
        print("3. Exit")

        choice = input("Enter your choice (1, 2, or 3): ")

        if choice == '1':
            encode_process()
        elif choice == '2':
            decode_process()
        elif choice == '3':
            print("Exiting the program. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def encode_process():
    print("\n--- Encoding Process ---")
    try:
        image_path = input("Enter the path to the original image (e.g., input.jpg): ")
        file_path = input("Enter the path to the file to hide (e.g., secret.txt): ")
        output_path = input("Enter the path for the output image (e.g., output.png): ")

        if not all([image_path, file_path, output_path]):
            print("All paths must be provided. Please try again.")
            return

        if not os.path.exists(image_path):
            print(f"Error: The image file '{image_path}' was not found.")
            return

        if not os.path.exists(file_path):
            print(f"Error: The file to hide '{file_path}' was not found.")
            return

        coder.coder(image_path, file_path, output_path)
        print(f"Successfully encoded '{file_path}' into '{output_path}'.")

    except Exception as e:
        print(f"An error occurred during encoding: {e}")

def decode_process():
    print("\n--- Decoding Process ---")
    try:
        image_path = input("Enter the path to the image to decode (e.g., output.png): ")
        output_path = input("Enter the path for the decoded file (e.g., decoded.txt): ")

        if not all([image_path, output_path]):
            print("All paths must be provided. Please try again.")
            return

        if not os.path.exists(image_path):
            print(f"Error: The image file '{image_path}' was not found.")
            return

        decoder.decoder(image_path, output_path)
        print(f"Successfully decoded a file from '{image_path}' to '{output_path}'.")

    except Exception as e:
        print(f"An error occurred during decoding: {e}")

if __name__ == "__main__":
    main()