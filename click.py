import time
import json
from pynput import mouse
from pywinauto.application import Application
from pywinauto.uia_element_info import UIAElementInfo
from pywinauto import Desktop, findwindows
import pyautogui



def rectangle_to_str(rect):
    return f"{int(rect.left)}-{int(rect.top)}-{int(rect.right)}-{int(rect.bottom)}"

def generate_composite_id(elem_info):
    """
    Build a composite ID from key properties.
    (You may adjust this format to suit your needs.)
    """
    control_type = elem_info.control_type or "UnknownControl"
    class_name = elem_info.class_name or "UnknownClass"
    auto_id = elem_info.automation_id if elem_info.automation_id else "NoAutomationId"
    name = elem_info.name if elem_info.name else "NoName"
    rect_str = rectangle_to_str(elem_info.rectangle)
    return f"{control_type}|{class_name}|{auto_id}|{name}|{rect_str}"

def dump_ui_tree(elem, depth=0):
    """
    Recursively dump the UI tree from the given UIAElementInfo object.
    Returns a dict with a composite ID and a list of children.
    """
    tree = {}
    tree["composite"] = generate_composite_id(elem)
    tree["children"] = []
    try:
        children = elem.children()
    except Exception:
        children = []
    for index, child in enumerate(children, start=1):
        child_composite = f"[{index}] " + generate_composite_id(child)
        subtree = dump_ui_tree(child, depth + 1)
        subtree["composite"] = child_composite
        tree["children"].append(subtree)
    return tree

def find_path_in_tree(tree, target_composite):
    """
    Search the dumped UI tree for a node whose "composite" matches target_composite.
    Returns a list of composite IDs from the root to the target if found.
    """
    if tree["composite"] == target_composite:
        return [target_composite]
    for child in tree["children"]:
        path = find_path_in_tree(child, target_composite)
        if path is not None:
            return [tree["composite"]] + path
    return None

def find_element_by_path(parent, path_list):
    """
    Starting at the given pywinauto wrapper 'parent', navigate through its children
    using the recorded composite IDs (path_list) and return the matching element.
    """
    if not path_list:
        return parent
    children = parent.children()
    for index, child in enumerate(children, start=1):
        composite = f"[{index}] " + generate_composite_id(child.element_info)
        if composite == path_list[0]:
            return find_element_by_path(child, path_list[1:])
    return None



# windows = Desktop(backend="uia").windows(title_re=".*Tableau.*", visible_only=True)
app = Application(backend="uia").connect(process=24008)
print("hello")
windows = app.windows()

if not windows:
    raise Exception("No Tableau windows found.")

# Select the main Tableau window by choosing the largest one.
def window_area(win):
    rect = win.rectangle()
    return (rect.right - rect.left) * (rect.bottom - rect.top)

tableau_window = max(windows, key=window_area)
print(f"Connected to Tableau window: Handle {tableau_window.handle}, Title: {tableau_window.window_text()}")

app = Application(backend="uia").connect(handle=tableau_window.handle)
main_window = app.window(handle=tableau_window.handle)

target_elem = find_element_by_path(main_window, ['Window|TMainWindow|NoAutomationId|Tableau - Book2 [Recovered]|-312--1411-2248--48', '[2] Group|CentralWidget|NoAutomationId|NoName|-312--1385-2248--48', '[3] ToolBar|ToolbarWidget|NoAutomationId|NoName|-312--1385-2248--1335', '[16] Button|TableauCommandButton|AffordanceId_Analysis_SwapRowsAndColumns|NoName|220--1379-257--1342', '[1] Image|QLabel|NoAutomationId|NoName|220--1379-257--1342'])
if target_elem is not None:
    print("Found target element. Performing click...")
    target_elem.click_input()
else:
    print("Could not locate the target element based on the recorded path.")

