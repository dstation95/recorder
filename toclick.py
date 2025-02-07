import os
import time
import json
import sys
from pynput import mouse
from pywinauto.application import Application
from pywinauto.uia_element_info import UIAElementInfo
from pywinauto import Desktop
import pyautogui
import openai
from openai import OpenAI  # Import the new OpenAI class

# ============================================================
# Step 0: Set DeepSeek API credentials
# ============================================================
# Either set the DEEPSEEK_API_KEY environment variable or enter it when prompted.
# (Be sure not to expose your API key in shared notebooks.)
openai.api_key = "sk-f5e4717920a34d75b05a219b8a7e5c14"
openai.api_base = "https://api.deepseek.com"

# ============================================================
# Step 1: Define Helper Functions for UI Snapshot
# ============================================================
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

# ============================================================
# Step 2: Get the Task Prompt and Load Example Files (if available)
# ============================================================
task_prompt = input("Enter the task prompt (e.g., 'swap x and y'): ")
file_prefix = task_prompt.lower().replace(" ", "_")
# Expected files (optional examples) – adjust as needed:
input_examples_file = f"{file_prefix}_input.jsonl"
output_examples_file = f"{file_prefix}_output.jsonl"

def load_examples(filename):
    examples = []
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        examples.append(json.loads(line.strip()))
                    except Exception as e:
                        print("Error parsing line in", filename, ":", e)
    return examples

input_examples = load_examples(input_examples_file)
output_examples = load_examples(output_examples_file)

example_text = ""
for inp, out in zip(input_examples, output_examples):
    # We assume each example's input has a "prompt" field and output has a "runtime_id"
    example_text += f"Example:\nInput: {json.dumps(inp, indent=2)}\nOutput: {json.dumps(out, indent=2)}\n\n"

# ============================================================
# Step 3: Connect to the Target Application Window (e.g., Tableau)
# ============================================================
windows = Desktop(backend="uia").windows(title_re=".*Tableau.*", visible_only=True)
if not windows:
    print("No Tableau window found.")
    sys.exit(1)

def window_area(win):
    rect = win.rectangle()
    return (rect.right - rect.left) * (rect.bottom - rect.top)

target_window = max(windows, key=window_area)
print(f"Connected to window: Handle {target_window.handle}, Title: {target_window.window_text()}")

app = Application(backend="uia").connect(handle=target_window.handle)
main_window = app.window(handle=target_window.handle)

# Capture a new screenshot and UI snapshot.
new_ui_tree = dump_ui_tree(main_window.element_info)
new_snapshot_str = json.dumps(new_ui_tree, indent=2)
new_screenshot = main_window.capture_as_image()
new_screenshot_filename = f"{file_prefix}_current.png"
new_screenshot.save(new_screenshot_filename)
print(f"New screenshot saved as {new_screenshot_filename}")

# ============================================================
# Step 4: Build the Full Prompt for Inference
# ============================================================
full_prompt = f"""
Below are examples of UI snapshots with their corresponding runtime IDs for the button click task.
{example_text}
Now, given the current UI snapshot and the instruction "{task_prompt}", return ONLY the runtime_id of the UI element that should be clicked.
Current UI snapshot:
{new_snapshot_str}
"""

# ============================================================
# Step 5: Call the DeepSeek API for Inference using client.chat.completions.create
# ============================================================
def deepseek_infer(prompt_text):
    # Create a client instance using the OpenAI SDK
    client = OpenAI(api_key=openai.api_key, base_url=openai.api_base)
    response = client.chat.completions.create(
         model="deepseek-chat",  # deepseek-chat invokes DeepSeek-V3
         messages=[
             {"role": "system", "content": "You are a UI automation assistant. Based on the given UI snapshot and instruction, return ONLY the runtime_id (as plain text) of the UI element to click."},
             {"role": "user", "content": prompt_text}
         ],
         stream=False
    )
    # Access the message content as per the new API interface:
    return response.choices[0].message["content"].strip()

predicted_runtime_id = deepseek_infer(full_prompt)
print("Predicted runtime ID:", predicted_runtime_id)

# ============================================================
# Step 6: Use Pywinauto to Find the Element by Runtime ID and Click It
# ============================================================
def search_for_runtime_id(wrapper, target_rt):
    try:
        comp = generate_composite_id(wrapper.element_info)
    except Exception:
        comp = ""
    current_rt = runtime_id_to_str(wrapper.element_info.runtime_id)
    if current_rt == target_rt:
        return wrapper
    for child in wrapper.children():
        found = search_for_runtime_id(child, target_rt)
        if found is not None:
            return found
    return None

target_elem = search_for_runtime_id(main_window, predicted_runtime_id)
if target_elem is not None:
    print("Found target element. Clicking it...")
    target_elem.click_input()
else:
    print("Could not locate the element with the predicted runtime ID.")
