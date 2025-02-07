from pywinauto import Application
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
    # Connect using the UI Automation backend ("uia")
    try:
        # Adjust the title_re if Tableau's window title is different.
        app = Application(backend="uia").connect(title_re=".*Tableau.*")
    except Exception as e:
        print("Could not connect to Tableau Desktop. Ensure it is running and its title contains 'Tableau'.")
        sys.exit(1)
    
    main_window = app.top_window()
    print("Connected to main window:", main_window.window_text())
    
    print("\nUI Element Tree:")
    print_tree(main_window)

if __name__ == "__main__":
    main()
