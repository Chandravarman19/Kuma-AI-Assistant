import pytesseract
from PIL import Image
import os

# Path to your screenshot
image_path = "active_window.png"

# Configure tesseract path (change if needed)
# If installed normally on Windows, use:
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def read_text_from_image(image_path):
    if not os.path.exists(image_path):
        print("❌ Screenshot not found.")
        return

    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    print("\n🧾 OCR Text Extracted:\n")
    print(text)

if __name__ == "__main__":
    read_text_from_image(image_path)
