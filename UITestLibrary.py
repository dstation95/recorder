# UITestLibrary.py
from pywinauto import Application
import sys

class UITestLibrary:
    def __init__(self):
        self.app = None
        self.main_window = None

    def connect_to_application(self, title_regex=".*Tableau.*"):
        """Connects to the running application matching the title regex."""
        try:
            self.app = Application(backend="uia").connect(title_re=title_regex)
            self.main_window = self.app.top_window()
            return f"Connected to: {self.main_window.window_text()}"
        except Exception as e:
            raise Exception(f"Could not connect to the application: {e}")

    def get_ui_tree(self):
        """Returns a string representation of the UI element tree."""
        if not self.main_window:
            raise Exception("Not connected to any application. Call 'Connect To Application' first.")
        lines = []
        def traverse(element, indent=0):
            try:
                elem_text = element.window_text()
            except Exception:
                elem_text = ""
            ctrl_type = element.element_info.control_type
            lines.append(" " * indent + f"{elem_text} ({ctrl_type})")
            try:
                for child in element.children():
                    traverse(child, indent + 2)
            except Exception:
                pass
        traverse(self.main_window)
        return "\n".join(lines)

    def click_button_by_name(self, button_name):
        """Finds a button by its Name property and clicks it."""
        if not self.main_window:
            raise Exception("Not connected to any application.")
        try:
            # Search for the button with matching title and control type "Button"
            button = self.main_window.child_window(title=button_name, control_type="Button")
            button.wait('visible', timeout=5)
            rect = button.rectangle()
            button.click_input()  # Use click_input for a simulated physical click.
            return f"Clicked '{button_name}' button at {rect}"
        except Exception as e:
            raise Exception(f"Failed to click button '{button_name}': {e}")

    def refresh_ui_tree(self):
        """Re-reads the UI tree after an interaction and returns the new tree."""
        # For a simple example, assume the window remains the same.
        return self.get_ui_tree()
