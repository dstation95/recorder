from pywinauto import Application
import pyautogui
from PIL import Image, ImageDraw
import pytesseract
import sys
import time

# Optionally set the Tesseract command if it's not in PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def get_composite_key(element):
    """
    Constructs a composite key for a UI element using available properties.
    This key is composed of:
      - ControlType
      - ClassName
      - AutomationId (if any)
      - The element's visible text (Name)
      - The bounding rectangle (normalized)
      - The runtime ID (for the session)
    """
    try:
        name = element.window_text().strip() or "NoName"
    except Exception:
        name = "NoName"
    ctrl_type = element.element_info.control_type or "UnknownType"
    class_name = element.element_info.class_name or "UnknownClass"
    automation_id = element.element_info.automation_id or "NoAutomationId"
    
    # Get the bounding rectangle as a string
    try:
        rect = element.rectangle()
        bounds_str = f"{rect.left}-{rect.top}-{rect.right}-{rect.bottom}"
    except Exception:
        bounds_str = "NoBounds"
    
    # Get runtime ID if available; join as underscore-separated string.
    runtime_id = getattr(element.element_info, 'runtime_id', None)
    if runtime_id:
        runtime_id_str = "_".join(str(x) for x in runtime_id)
    else:
        runtime_id_str = "NoRuntimeId"
    
    # Composite key: you can adjust the order and delimiter as needed.
    composite_key = f"{ctrl_type}|{class_name}|{automation_id}|{name}|{bounds_str}|{runtime_id_str}"
    return composite_key

def collect_elements_with_keys(root):
    """
    Traverses the UI tree from the given root and returns a dictionary mapping
    composite keys to the corresponding UI element objects.
    """
    mapping = {}
    def traverse(element):
        key = get_composite_key(element)
        mapping[key] = element
        try:
            for child in element.children():
                traverse(child)
        except Exception:
            pass
    traverse(root)
    return mapping

def draw_highlight(bounds, outline_color="red", width=3):
    """
    Captures the current screen, draws a rectangle around the provided bounds,
    and returns the modified image.
    """
    screenshot = pyautogui.screenshot()
    draw = ImageDraw.Draw(screenshot)
    draw.rectangle(bounds, outline=outline_color, width=width)
    return screenshot

def perform_ocr(bounds):
    """
    Captures the current screen, crops to the given bounds, and performs OCR on that region.
    """
    screenshot = pyautogui.screenshot()
    cropped = screenshot.crop(bounds)
    text = pytesseract.image_to_string(cropped)
    return text

def main():
    try:
        # Adjust the title_re to match your target application's window title.
        app = Application(backend="uia").connect(title_re=".*Tableau.*")
    except Exception as e:
        print("Could not connect to Tableau Desktop. Ensure it is running and its title contains 'Tableau'.")
        sys.exit(1)
    
    main_window = app.top_window()
    print("Connected to main window:", main_window.window_text())
    
    # Collect all elements and their composite keys from the UI tree.
    print("\nCollecting UI elements (this might take a moment)...")
    mapping = collect_elements_with_keys(main_window)
    print(f"Collected {len(mapping)} elements.\n")
    
    # Print out the composite keys (or a subset) for review.
    for idx, key in enumerate(mapping.keys()):
        # Only print the first 50 for brevity (or print all if desired)
        if idx < 50:
            print(f"[{idx}] {key}\n")
        else:
            break

    print("\nYou can now enter a substring from one of the composite keys above.")
    search_substring = input("Enter a substring to search for a UI element: ").strip()
    
    # Find matching keys (if more than one, list them)
    matching_keys = [key for key in mapping.keys() if search_substring in key]
    
    if not matching_keys:
        print("No matching elements found with that substring.")
        sys.exit(1)
    
    print(f"Found {len(matching_keys)} matching elements:")
    for i, key in enumerate(matching_keys):
        print(f"[{i}] {key}")
    
    try:
        selected_index = int(input("Enter the index number of the element you want to highlight: "))
        selected_key = matching_keys[selected_index]
    except Exception as e:
        print("Invalid input:", e)
        sys.exit(1)
    
    element = mapping[selected_key]
    try:
        bounds_obj = element.rectangle()
        bounds = (bounds_obj.left, bounds_obj.top, bounds_obj.right, bounds_obj.bottom)
    except Exception as e:
        print("Error retrieving bounds:", e)
        sys.exit(1)
    
    print(f"Highlighting element with composite key:\n{selected_key}")
    print("Bounds:", bounds)
    
    # Draw the highlight on a screenshot
    highlighted_img = draw_highlight(bounds)
    highlighted_img.show()  # Opens the image viewer
    highlighted_img.save("highlighted_element.png")
    
    # Perform OCR on that region and print the extracted text
    ocr_text = perform_ocr(bounds)
    print("\nOCR Text from highlighted region:")
    print(ocr_text)
    
if __name__ == "__main__":
    main()
