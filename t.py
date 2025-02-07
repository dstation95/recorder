from pywinauto import Application
import sys
import time

def print_tree(element, indent=0):
    """Recursively prints the UI element tree with available properties, including RuntimeId if present."""
    indent_str = " " * (indent * 2)
    
    # Retrieve the element's name; if not available, use empty string
    try:
        name = element.window_text()
    except Exception:
        name = ""
    
    # Get control type and automation id from element_info
    ctrl_type = element.element_info.control_type
    automation_id = element.element_info.automation_id
    
    # Attempt to retrieve help text; if not available, use "N/A"
    help_text = getattr(element.element_info, 'help_text', None)
    if help_text is None:
        help_text = "N/A"
    
    # Attempt to retrieve runtime id; if not available, use "N/A"
    runtime_id = getattr(element.element_info, 'runtime_id', None)
    if runtime_id is None:
        runtime_id_str = "N/A"
    else:
        # runtime_id is often a tuple or list of integers; convert it to a string
        runtime_id_str = str(runtime_id)
    
    # Get the bounding rectangle
    try:
        bounding_rect = element.rectangle()
    except Exception:
        bounding_rect = "N/A"
    
    # Print detailed information about the element
    print(f"{indent_str}Name         : {name}")
    print(f"{indent_str}Type         : {ctrl_type}")
    print(f"{indent_str}AutomationId : {automation_id}")
    print(f"{indent_str}HelpText     : {help_text}")
    print(f"{indent_str}RuntimeId    : {runtime_id_str}")
    print(f"{indent_str}Bounds       : {bounding_rect}\n")
    
    # Recursively print children
    try:
        for child in element.children():
            print_tree(child, indent + 1)
    except Exception:
        pass

def main():
    try:
        # Connect using the UI Automation ("uia") backend.
        # Adjust the title regular expression as needed.
        app = Application(backend="uia").connect(title_re=".*Tableau.*")
    except Exception as e:
        print("Could not connect to Tableau Desktop. Ensure it is running and its title contains 'Tableau'.")
        sys.exit(1)
    
    main_window = app.top_window()
    print("Connected to main window:", main_window.window_text())
    
    print("\nDetailed UI Element Tree:")
    print_tree(main_window)
    
    # Prompt user to click a button
    button_name = input("\nEnter the exact name of the button to click: ")
    try:
        # Locate the button by filtering on title and control type "Button"
        button = main_window.child_window(title=button_name, control_type="Button")
        button.wait('visible', timeout=5)
        rect = button.rectangle()
        print(f"\nFound '{button_name}' button at {rect}. Clicking it now...")
        button.click_input()
    except Exception as e:
        print(f"Error: Could not find or click button '{button_name}'. Exception: {e}")
        sys.exit(1)
    
    # Wait a short time for the UI to update
    time.sleep(2)
    print("\nUpdated Detailed UI Element Tree:")
    print_tree(main_window)

if __name__ == "__main__":
    main()
