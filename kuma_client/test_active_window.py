import pygetwindow as gw
import time

def get_active_window_title():
    try:
        win = gw.getActiveWindow()
        if win:
            return win.title
        else:
            return "No active window detected."
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    print("🪟 Tracking active window... (Press Ctrl+C to stop)\n")
    while True:
        title = get_active_window_title()
        print(f"➡️ Active Window: {title}")
        time.sleep(2)
