import pygetwindow as gw
import pyautogui
import time

def screenshot_active_window():
    try:
        win = gw.getActiveWindow()
        if not win:
            print("❌ No active window found.")
            return

        left, top, right, bottom = win.left, win.top, win.right, win.bottom
        screenshot = pyautogui.screenshot(region=(left, top, right - left, bottom - top))
        screenshot.save("active_window.png")
        print(f"✅ Screenshot saved for: {win.title}")
    except Exception as e:
        print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    print("📸 Capturing active window in 3 seconds...")
    time.sleep(3)
    screenshot_active_window()
