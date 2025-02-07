from pywinauto import Application
import time
import sys

def print_tree(element, indent=0):
    """Recursively prints the UI element tree."""
    try:
        elem_text = element.window_text()
    except Exception:
        elem_text = ""
    ctrl_type = element.element_info.control_type
    print(" " * indent + f"{elem_text} ({ctrl_type})")
    try:
        for child in element.children():
            print_tree(child, indent + 2)
    except Exception:
        pass

def main():
    # Connect to Tableau Desktop (adjust the regex if needed).
    try:
        # This uses the "uia" backend (based on Microsoft UI Automation)
        app = Application(backend="uia").connect(title_re=".*Tableau.*")
    except Exception as e:
        print("Could not connect to Tableau Desktop.")
        print("Ensure that Tableau is running and its window title contains 'Tableau'.")
        sys.exit(1)
    
    main_window = app.top_window()
    print("Connected to main window:", main_window.window_text())
    
    print("\nInitial UI Element Tree:")
    print_tree(main_window)
    
    # Prompt the user for the name of the button to click.
    # For example, if you want to click a button named "Close" or "Show Me", type that.
    button_name = input("\nEnter the exact name of the button to click: ")
    
    try:
        # Locate the button by its title and control type "Button"
        button = main_window.child_window(title=button_name, control_type="Button")
        button.wait('visible', timeout=5)
        rect = button.rectangle()
        print(f"Found '{button_name}' button at {rect}. Clicking now...")
        button.click_input()  # Simulates a real physical click.
    except Exception as e:
        print(f"Error: Could not find or click button '{button_name}'. Exception: {e}")
        sys.exit(1)
        
    # Wait a short time to allow the UI to update after the click.
    time.sleep(2)
    
    print("\nUpdated UI Element Tree:")
    print_tree(main_window)

if __name__ == "__main__":
    main()
