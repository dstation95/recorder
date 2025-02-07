import time
import json
import sys
from pynput import mouse
from pywinauto.application import Application
from pywinauto.uia_element_info import UIAElementInfo
from pywinauto import Desktop
import pyautogui

# (A) Prompt for task instruction.
instruction = input("Enter the task instruction (e.g., 'Click the x and y axis swap button'): ")

# (B) Connect to the target application.
# Adjust the title regex to match your application window (here assumed to be Tableau).
windows = Desktop(backend="uia").windows(title_re=".*Tableau.*", visible_only=True)
if not windows:
    print("No Tableau window found.")
    sys.exit(1)

def window_area(win):
    rect = win.rectangle()
    return (rect.right - rect.left) * (rect.bottom - rect.top)

tableau_window = max(windows, key=window_area)
print(f"Connected to Tableau window: Handle {tableau_window.handle}, Title: {tableau_window.window_text()}")

app = Application(backend="uia").connect(handle=tableau_window.handle)
main_window = app.window(handle=tableau_window.handle)

# (C) Helper functions to build composite IDs that now include runtime ID.
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

# (D) Take an initial screenshot of the main window and dump the UI tree.
initial_img = main_window.capture_as_image()
initial_img_filename = "tableau_initial.png"
initial_img.save(initial_img_filename)
print(f"Initial screenshot saved as {initial_img_filename}")

ui_tree = dump_ui_tree(main_window.element_info)
tree_timestamp = int(time.time())
tree_filename = f"ui_tree_{tree_timestamp}.json"
with open(tree_filename, "w") as f:
    json.dump(ui_tree, f, indent=2)
print(f"UI tree snapshot saved as {tree_filename}")

# (E) Build the training input JSON.
training_input = {
    "ui_snapshot": ui_tree,
    "instruction": instruction
}
with open("training_input.json", "w") as f:
    json.dump(training_input, f, indent=2)
print("Training input saved to training_input.json")

# --- Step 2: Wait for a Click and Record the Output ---
recorded_runtime_id = None

def on_click(x, y, button, pressed):
    global recorded_runtime_id
    if pressed:
        click_data = {"x": x, "y": y, "button": str(button)}
        print(f"Click detected at: {click_data}")
        # Ensure the click is within the main window.
        rect = main_window.rectangle()
        if not (rect.left <= x <= rect.right and rect.top <= y <= rect.bottom):
            print("Click outside application window; ignoring.")
            return False
        # Wait 0.5 seconds after the click.
        time.sleep(0.5)
        try:
            clicked_elem_info = UIAElementInfo.from_point(x, y)
        except Exception as e:
            print("Error retrieving element info:", e)
            return False
        composite = generate_composite_id(clicked_elem_info)
        print("Recorded composite ID:", composite)
        # Extract the runtime ID (the last field).
        recorded_runtime_id = composite.split("|")[-1]
        print("Extracted runtime ID:", recorded_runtime_id)
        return False

with mouse.Listener(on_click=on_click) as listener:
    listener.join()

# Additional wait before finishing.
time.sleep(1)
if recorded_runtime_id is None:
    print("No runtime ID was recorded.")
    sys.exit(1)

training_output = {
    "runtime_id": recorded_runtime_id
}
with open("training_output.json", "w") as f:
    json.dump(training_output, f, indent=2)
print("Training output saved to training_output.json")