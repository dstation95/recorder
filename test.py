from pywinauto import Application
import pyautogui
from PIL import Image, ImageDraw, ImageFont
import pytesseract  # Optional: for OCR
import sys
import time

def get_element_bounds(element):
    """
    Returns the bounding rectangle of an element as a tuple: (left, top, right, bottom)
    """
    try:
        rect = element.rectangle()
        return (rect.left, rect.top, rect.right, rect.bottom)
    except Exception as e:
        print("Error getting rectangle:", e)
        return None

def draw_rectangle_on_screenshot(bounds, outline_color="red", width=3):
    """
    Takes a screenshot, draws a rectangle at the given bounds, and shows the image.
    """
    # Capture the entire screen
    screenshot = pyautogui.screenshot()
    draw = ImageDraw.Draw(screenshot)
    draw.rectangle(bounds, outline=outline_color, width=width)
    return screenshot

def perform_ocr_on_region(image, bounds):
    """
    Crops the image to the bounds and performs OCR.
    """
    cropped = image.crop(bounds)
    # Optionally, specify tesseract cmd path if not in PATH:
    # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    text = pytesseract.image_to_string(cropped)
    return text

def main():
    try:
        # Connect to the target application. Adjust title_re as needed.
        app = Application(backend="uia").connect(title_re=".*Tableau.*")
    except Exception as e:
        print("Could not connect to the application. Ensure it is running and the title matches:", e)
        sys.exit(1)
    
    main_window = app.top_window()
    print("Connected to main window:", main_window.window_text())
    
    # For demonstration, use print_control_identifiers() to see the UI tree.
    # (In practice, you might narrow it down by known properties.)
    try:
        main_window.print_control_identifiers()
    except Exception as e:
        print("Error printing control identifiers:", e)
    
    # Prompt the user for the button or element to highlight
    element_name = input("Enter the exact name of the element to highlight: ")
    
    try:
        # Try to locate the element by name and a control type (for example, Button or Image)
        # Adjust control_type as needed
        element = main_window.child_window(title=element_name)
        element.wait('visible', timeout=10)
    except Exception as e:
        print("Error: Could not locate element named '{}'. Exception: {}".format(element_name, e))
        sys.exit(1)
    
    bounds = get_element_bounds(element)
    if not bounds:
        print("Could not retrieve bounds for element.")
        sys.exit(1)
    
    print("Element bounds:", bounds)
    
    # Capture screenshot and draw bounding rectangle
    screenshot = draw_rectangle_on_screenshot(bounds)
    
    # Optionally, display OCR result for the region
    try:
        ocr_text = perform_ocr_on_region(screenshot, bounds)
        print("OCR text from the region:\n", ocr_text)
    except Exception as e:
        print("Error during OCR:", e)
    
    # Show the image with the highlighted element
    screenshot.show()
    
    # Optionally, save the image for later reference
    screenshot.save("highlighted_element.png")
    
if __name__ == "__main__":
    main()
