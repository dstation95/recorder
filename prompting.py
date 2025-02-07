import os
import time
import json
import sys
from pynput import mouse
from pywinauto.application import Application
from pywinauto.uia_element_info import UIAElementInfo
from pywinauto import Desktop
import pyautogui

# ------------------------------------------------------------
# Step 1: Get the system prompt and derive file names
# ------------------------------------------------------------
# Prompt the user for a system prompt (e.g., "swap x and y")
prompt_text = input("Enter the system prompt for this recording (e.g., 'swap x and y'): ")
# Normalize the prompt to create a safe file prefix (lowercase, underscores instead of spaces)
file_prefix = prompt_text.lower().replace(" ", "_")

# Define file names for the training examples (using JSON Lines format)
input_filename = f"{file_prefix}_input.jsonl"    # e.g., swap_x_and_y_input.jsonl
output_filename = f"{file_prefix}_output.jsonl"  # e.g., swap_x_and_y_output.jsonl

# ------------------------------------------------------------
# Step 2: Connect to the Application Window (e.g., Tableau)
# ------------------------------------------------------------
# Adjust the title regex to match your target application (e.g., Tableau)
windows = Desktop(backend="uia").windows(title_re=".*Tableau.*", visible_only=True)
if not windows:
    print("No Tableau window found.")
    sys.exit(1)

def window_area(win):
    rect = win.rectangle()
    return (rect.right - rect.left) * (rect.bottom - rect.top)

# Choose the largest visible window
target_window = max(windows, key=window_area)
print(f"Connected to window: Handle {target_window.handle}, Title: {target_window.window_text()}")

app = Application(backend="uia").connect(handle=target_window.handle)
main_window = app.window(handle=target_window.handle)

# ------------------------------------------------------------
# Step 3: Capture Initial Screenshot and UI Snapshot
# ------------------------------------------------------------
def rectangle_to_str(rect):
    return f"{int(rect.left)}-{int(rect.top)}-{int(rect.right)}-{int(rect.bottom)}"

def runtime_id_to_str(runtime_id):
    if runtime_id:
        return "_".join(str(item) for item in runtime_id)
    return "NoRuntimeID"

def generate_composite_id(elem_info):
    control_type = elem_info.control_type or "UnknownControl"
    class_name = elem_info.class_name or "UnknownClass"
    auto_id = elem_info.automation_id if elem_info.automation_id else "NoAutomationId"
    name = elem_info.name if elem_info.name else "NoName"
    rect_str = rectangle_to_str(elem_info.rectangle)
    rt_str = runtime_id_to_str(elem_info.runtime_id)
    return f"{control_type}|{class_name}|{auto_id}|{name}|{rect_str}|{rt_str}"

def dump_ui_tree(elem_info):
    tree = {}
    tree["composite"] = generate_composite_id(elem_info)
    tree["children"] = []
    try:
        children = elem_info.children()
    except Exception:
        children = []
    for index, child in enumerate(children, start=1):
        child_composite = f"[{index}] " + generate_composite_id(child)
        subtree = dump_ui_tree(child)
        subtree["composite"] = child_composite
        tree["children"].append(subtree)
    return tree

# Capture a screenshot of the main window
initial_img = main_window.capture_as_image()
initial_img_filename = f"{file_prefix}_initial.png"
initial_img.save(initial_img_filename)
print(f"Initial screenshot saved as {initial_img_filename}")

# Dump the UI tree snapshot
ui_tree = dump_ui_tree(main_window.element_info)
tree_timestamp = int(time.time())
tree_filename = f"{file_prefix}_ui_tree_{tree_timestamp}.json"
with open(tree_filename, "w") as f:
    json.dump(ui_tree, f, indent=2)
print(f"UI tree snapshot saved as {tree_filename}")

# Build the training input JSON object
training_input = {
    "ui_snapshot": ui_tree,
    "prompt": prompt_text
}

# Append the training input to the input file (JSONL)
with open(input_filename, "a") as f:
    json.dump(training_input, f)
    f.write("\n")
print(f"Appended training input to {input_filename}")

# ------------------------------------------------------------
# Step 4: Wait for a Click and Record the Output (Runtime ID)
# ------------------------------------------------------------
recorded_runtime_id = None

def on_click(x, y, button, pressed):
    global recorded_runtime_id
    if pressed:
        click_data = {"x": x, "y": y, "button": str(button)}
        print(f"Click detected at: {click_data}")
        # Ensure the click is inside the main window
        rect = main_window.rectangle()
        if not (rect.left <= x <= rect.right and rect.top <= y <= rect.bottom):
            print("Click outside window; ignoring.")
            return False
        # Wait 0.5 seconds after the click before recording
        time.sleep(0.5)
        try:
            clicked_elem_info = UIAElementInfo.from_point(x, y)
        except Exception as e:
            print("Error retrieving element info:", e)
            return False
        composite = generate_composite_id(clicked_elem_info)
        print("Recorded composite ID:", composite)
        # Extract runtime ID (the last field after splitting by '|')
        recorded_runtime_id = composite.split("|")[-1]
        print("Extracted runtime ID:", recorded_runtime_id)
        return False  # Stop the mouse listener

with mouse.Listener(on_click=on_click) as listener:
    listener.join()

# Wait an extra second before finishing.
time.sleep(1)
if recorded_runtime_id is None:
    print("No runtime ID recorded.")
    sys.exit(1)

training_output = {
    "runtime_id": recorded_runtime_id
}

# Append the training output to the output file (JSONL)
with open(output_filename, "a") as f:
    json.dump(training_output, f)
    f.write("\n")
print(f"Appended training output to {output_filename}")
