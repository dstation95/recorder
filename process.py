from pywinauto import Application
import pyautogui
from PIL import Image, ImageDraw
import pytesseract
import sys
import time

# Optionally, set the Tesseract command if it's not in PATH:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def format_runtime_id(runtime_id):
    """
    Format the runtime id as a string like "(42, 67584, 3, -2147483647, 67584, -2, 5)".
    """
    if runtime_id is None:
        return "N/A"
    try:
        return "(" + ", ".join(str(item) for item in runtime_id) + ")"
    except Exception as e:
        return str(runtime_id)

def get_composite_key(element):
    """
    Constructs a composite key for an element using available properties.
    Here we include:
      - ProcessId
      - ControlType
      - ClassName
      - Name (visible text)
      - Bounding Rectangle
      - RuntimeId (formatted like Inspect.exe output)
    """
    # Process ID (if available)
    process_id = getattr(element.element_info, 'process_id', "NoProcessId")
    
    try:
        name = element.window_text().strip() or "NoName"
    except Exception:
        name = "NoName"
    
    ctrl_type = element.element_info.control_type or "UnknownType"
    class_name = element.element_info.class_name or "UnknownClass"
    
    # Get bounding rectangle as a string
    try:
        rect = element.rectangle()
        bounds_str = f"{rect.left},{rect.top},{rect.right},{rect.bottom}"
    except Exception:
        bounds_str = "NoBounds"
    
    # Get runtime ID and format it like Inspect.exe
    runtime_id = getattr(element.element_info, 'runtime_id', None)
    runtime_id_str = format_runtime_id(runtime_id)
    
    # Composite key: you can adjust the order and delimiter as needed.
    composite_key = f"PID:{process_id}|{ctrl_type}|{class_name}|{name}|{bounds_str}|{runtime_id_str}"
    return composite_key

def collect_elements_by_runtime_id(root):
    """
    Traverses the UI tree starting at 'root' and returns a dictionary mapping
    the formatted runtime ID (as a string) to the element.
    """
    mapping = {}
    def traverse(element):
        rid = format_runtime_id(getattr(element.element_info, 'runtime_id', None))
        # Note: If two elements share the same runtime ID (which ideally should not happen),
        # the last one encountered will be stored.
        mapping[rid] = element
        try:
            for child in element.children():
                traverse(child)
        except Exception:
            pass
    traverse(root)
    return mapping

def draw_highlight(bounds, outline_color="red", width=3):
    """
    Captures the screen, draws a rectangle around the provided bounds,
    and returns the modified image.
    """
    screenshot = pyautogui.screenshot()
    draw = ImageDraw.Draw(screenshot)
    draw.rectangle(bounds, outline=outline_color, width=width)
    return screenshot

def perform_ocr(bounds):
    """
    Captures the screen, crops to the specified bounds, and performs OCR on that region.
    """
    screenshot = pyautogui.screenshot()
    cropped = screenshot.crop(bounds)
    text = pytesseract.image_to_string(cropped)
    return text

def main():
    try:
        # Connect using the UI Automation ("uia") backend.
        # Adjust title_re to match your target application's window title (e.g., Tableau)
        app = Application(backend="uia").connect(title_re=".*Tableau.*", visible_only=False)
    except Exception as e:
        print("Could not connect to the target application. Ensure it is running and the title is correct.")
        sys.exit(1)
    
    main_window = app.top_window()
    print("Connected to main window:", main_window.window_text())
    
    # Collect elements keyed by their formatted runtime ID
    print("\nCollecting UI elements by runtime ID (this may take a moment)...")
    mapping = collect_elements_by_runtime_id(main_window)
    print(f"Collected {len(mapping)} elements.\n")
    
    # Print out the list of runtime IDs for review
    for idx, rid in enumerate(mapping.keys()):
        print(f"[{idx}] RuntimeID: {rid}\n")
    
    # Prompt the user to enter a runtime ID (or a substring of it)
    search_str = input("\nEnter the runtime ID or a substring to search for an element: ").strip()
    
    # Find matching runtime IDs (if more than one, list them)
    matching_keys = [rid for rid in mapping.keys() if search_str in rid]
    
    if not matching_keys:
        print("No matching elements found with that runtime ID substring.")
        sys.exit(1)
    
    print(f"\nFound {len(matching_keys)} matching elements:")
    for i, rid in enumerate(matching_keys):
        print(f"[{i}] {rid}")
    
    try:
        selected_index = int(input("\nEnter the index number of the element you want to highlight: "))
        selected_rid = matching_keys[selected_index]
    except Exception as e:
        print("Invalid input:", e)
        sys.exit(1)
    
    element = mapping[selected_rid]
    try:
        bounds_obj = element.rectangle()
        bounds = (bounds_obj.left, bounds_obj.top, bounds_obj.right, bounds_obj.bottom)
    except Exception as e:
        print("Error retrieving bounds for the selected element:", e)
        sys.exit(1)
    
    print("\nSelected element runtime ID:")
    print(selected_rid)
    print("Bounds:", bounds)
    
    # Draw highlight on a screenshot
    highlighted_img = draw_highlight(bounds)
    highlighted_img.show()  # This will open the default image viewer
    highlighted_img.save("highlighted_element.png")
    
    # Perform OCR on that region and print the result
    ocr_text = perform_ocr(bounds)
    print("\nOCR extracted text from the highlighted region:")
    print(ocr_text)

if __name__ == "__main__":
    main()
