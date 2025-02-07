import time
import json
from pynput import mouse
from pywinauto.application import Application
from pywinauto.uia_element_info import UIAElementInfo
from pywinauto import Desktop, findwindows
import pyautogui

# ---------------------------
# 1. Connect to the Tableau Window (or your Klio app window)
# ---------------------------
# Adjust the title regex to match your application window.
windows = Desktop(backend="uia").windows(title_re=".*Tableau.*", visible_only=True)
if not windows:
    raise Exception("No Tableau windows found.")

def window_area(win):
    rect = win.rectangle()
    return (rect.right - rect.left) * (rect.bottom - rect.top)

tableau_window = max(windows, key=window_area)
print(f"Connected to Tableau window: Handle {tableau_window.handle}, Title: {tableau_window.window_text()}")

app = Application(backend="uia").connect(handle=tableau_window.handle)
main_window = app.window(handle=tableau_window.handle)

# ---------------------------
# 2. Helper Functions: Composite ID (with runtime ID)
# ---------------------------
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

# ---------------------------
# 3. Pre-Recording: Take an Initial Screenshot and Dump UI Tree
# ---------------------------
initial_img = main_window.capture_as_image()
initial_img_filename = "tableau_initial.png"
initial_img.save(initial_img_filename)
print(f"Initial Tableau screenshot saved as {initial_img_filename}")

ui_tree = dump_ui_tree(main_window.element_info)
tree_timestamp = int(time.time())
tree_filename = f"ui_tree_{tree_timestamp}.json"
with open(tree_filename, "w") as f:
    json.dump(ui_tree, f, indent=2)
print(f"UI tree snapshot saved as {tree_filename}")

# ---------------------------
# 4. Recording Phase: Wait for a Click, Record the Element, and Take Final Screenshot
# ---------------------------
def record_click_and_composite(x, y, button, pressed):
    if pressed:
        click_data = {"x": x, "y": y, "button": str(button)}
        print(f"Click at: {click_data}")

        rect = main_window.rectangle()
        if not (rect.left <= x <= rect.right and rect.top <= y <= rect.bottom):
            print("Click outside application window; ignoring.")
            return

        # Wait 0.5 seconds after the click before taking the final screenshot.
        time.sleep(0.5)
        final_img = main_window.capture_as_image()
        timestamp = int(time.time())
        final_screenshot_filename = f"tableau_final_{timestamp}.png"
        final_img.save(final_screenshot_filename)
        print(f"Final Tableau screenshot saved as {final_screenshot_filename}")

        try:
            clicked_elem_info = UIAElementInfo.from_point(x, y)
        except Exception as e:
            print("Error retrieving element info:", e)
            return

        parent_info = clicked_elem_info.parent
        sibling_index = 0
        if parent_info:
            try:
                siblings = parent_info.children()
                sibling_index = siblings.index(clicked_elem_info) + 1
            except Exception:
                sibling_index = 0

        composite_id = f"[{sibling_index}] " + generate_composite_id(clicked_elem_info)
        print("Composite ID for the clicked element:")
        print(composite_id)

        record = {
            "timestamp": timestamp,
            "initial_screenshot": initial_img_filename,
            "final_screenshot": final_screenshot_filename,
            "ui_tree_file": tree_filename,
            "composite_id": composite_id,
            "click": click_data
        }
        with open("click_records.jsonl", "a") as f:
            f.write(json.dumps(record) + "\n")
        print("Recorded click (with composite ID) saved to click_records.jsonl")
        
        # Wait an additional 1 second before finishing.
        time.sleep(1)
        return False

with mouse.Listener(on_click=record_click_and_composite) as listener:
    listener.join()

# ---------------------------
# 5. Replay Phase: Locate the Element Using the Recorded Runtime ID and Click It
# ---------------------------
def replay_click(record):
    if "composite_id" not in record:
        print("Record does not contain 'composite_id'. Available keys:", record.keys())
        return

    target_composite = record["composite_id"]
    print("Replaying click using composite ID:")
    print(target_composite)
    
    def search_tree(wrapper):
        try:
            comp = generate_composite_id(wrapper.element_info)
        except Exception:
            comp = ""
        # Compare the runtime ID parts (the last field) of the composite strings.
        recorded_rt = target_composite.split("|")[-1]
        current_rt = runtime_id_to_str(wrapper.element_info.runtime_id)
        if recorded_rt == current_rt:
            return wrapper
        for child in wrapper.children():
            found = search_tree(child)
            if found is not None:
                return found
        return None

    target_elem = search_tree(main_window)
    if target_elem is not None:
        print("Found target element. Performing click...")
        target_elem.click_input()
    else:
        print("Could not locate the target element based on the recorded composite ID.")

# Example: Read the first record from click_records.jsonl and replay the click.
try:
    with open("click_records.jsonl", "r") as f:
        first_record = json.loads(f.readline().strip())
    # Wait briefly before replaying to allow any UI changes.
    time.sleep(1)
    replay_click(first_record)
except Exception as e:
    print("Error during replay:", e)
