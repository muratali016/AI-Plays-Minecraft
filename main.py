import pyautogui 
import time
import base64
from openai import OpenAI
import os
from PIL import Image
import io
from datetime import datetime
import keyboard
import win32gui
import win32con
import ctypes
import win32process
import win32api

client = OpenAI(api_key="sk-proj-xxx")

SCREENSHOT_FOLDER = "minecraft_screenshots"
if not os.path.exists(SCREENSHOT_FOLDER):
    os.makedirs(SCREENSHOT_FOLDER)

# Function to find Minecraft window
def find_minecraft_window(window_title="Minecraft"):
    result = []
    
    def window_enum_callback(hwnd, results):
        if win32gui.IsWindowVisible(hwnd) and window_title.lower() in win32gui.GetWindowText(hwnd).lower():
            results.append((hwnd, win32gui.GetWindowText(hwnd)))
        return True
    
    win32gui.EnumWindows(window_enum_callback, result)
    
    if result:
        print(f"Found Minecraft windows: {result}")
        return result[0][0]  # Return the first window handle found
    else:
        print(f"No window containing '{window_title}' found")
        return None


def focus_game_window(window_handle):
    if not window_handle:
        print("No window handle provided, cannot focus")
        return False
        
    try:
        
        print("Focusing window (Method 1)...")
        win32gui.ShowWindow(window_handle, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(window_handle)
        
        
        print("Focusing window (Method 2)...")
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        
        
        current_thread = win32api.GetCurrentThreadId()
        window_thread = win32process.GetWindowThreadProcessId(window_handle)[0]
        
        
        user32.AttachThreadInput(current_thread, window_thread, True)
        
        
        user32.SetWindowPos(window_handle, ctypes.c_int(win32con.HWND_TOPMOST), 0, 0, 0, 0, 
                           win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        user32.SetWindowPos(window_handle, ctypes.c_int(win32con.HWND_NOTOPMOST), 0, 0, 0, 0, 
                           win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        user32.SetForegroundWindow(window_handle)
        user32.BringWindowToTop(window_handle)
        user32.SetFocus(window_handle)
        user32.SetActiveWindow(window_handle)
        
        
        user32.AttachThreadInput(current_thread, window_thread, False)
        
        window_name = win32gui.GetWindowText(window_handle)
        print(f"Focused window: {window_name}")
        
        
        active_window = win32gui.GetForegroundWindow()
        active_window_name = win32gui.GetWindowText(active_window)
        print(f"Active window is now: {active_window_name}")
        
        if active_window == window_handle:
            print("Successfully focused window!")
            time.sleep(0.5)  # Short delay to ensure window is focused
            return True
        else:
            print("Warning: Window focus failed! Expected window not active.")
            return False
    except Exception as e:
        print(f"Error focusing window: {e}")
        return False


def capture_window_screenshot(window_handle=None):
    if window_handle:
        try:
            # Get window position and size
            x, y, x1, y1 = win32gui.GetWindowRect(window_handle)
            width = x1 - x
            height = y1 - y
            
            # Capture that specific region
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            print(f"Captured screenshot of window at {x},{y} with size {width}x{height}")
        except Exception as e:
            print(f"Error capturing window: {e}")
            screenshot = pyautogui.screenshot()  # Fallback to full screen
            print("Falling back to full screen screenshot")
    else:
        
        screenshot = pyautogui.screenshot()
        print("Taking full screen screenshot (no specific window found)")
    
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(SCREENSHOT_FOLDER, f"minecraft_{timestamp}.png")
    screenshot.save(filename)
    print(f"Saved screenshot: {filename}")
    
    
    buffered = io.BytesIO()
    screenshot.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    return img_str, screenshot


def get_minecraft_analysis(image_base64):
    try:
        # Updated system prompt to include mouse movement instructions.
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional Minecraft player assistant. Analyze the game state and provide strategic advice.\n\n"
                        "Observe the following elements:\n"
                        "1. Player surroundings (biome, structures, mobs)\n"
                        "2. Player inventory and equipped items\n"
                        "3. Player health, hunger, and experience\n"
                        "4. Time of day and weather conditions\n"w
                        "5. Any visible threats or opportunities\n\n"
                        "Based on what you see, recommend ONE clear action. "
                        "Your response can be one of the following commands for key presses: 'go', 'enter', 'space', "
                        "or one of these for mouse movements: 'rotate_left', 'rotate_right', 'rotate_up', 'rotate_down'. "
                        "Provide ONLY the single command word and NO other text."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=10
        )
        command = response.choices[0].message.content.strip().lower()
        print(f"AI analysis returned: '{command}'")
        return command
    except Exception as e:
        print(f"Error with API call: {e}")
        return None


def execute_mouse_movement(command):
    # Define movement deltas; adjust these values to match your in-game sensitivity
    delta = 50  # pixels to move; you might need to adjust for finer or coarser control
    if command == "rotate_left":
        pyautogui.moveRel(-delta, 0, duration=0.2)
        print("Moved mouse left")
    elif command == "rotate_right":
        pyautogui.moveRel(delta, 0, duration=0.2)
        print("Moved mouse right")
    elif command == "rotate_up":
        pyautogui.moveRel(0, -delta, duration=0.2)
        print("Moved mouse up")
    elif command == "rotate_down":
        pyautogui.moveRel(0, delta, duration=0.2)
        print("Moved mouse down")
    else:
        print("Unknown mouse command.")


def execute_command(command, window_handle):
    
    focus_success = focus_game_window(window_handle)
    if not focus_success:
        print("Warning: Could not focus game window. Attempting command execution anyway.")
    
    
    if command in ["rotate_left", "rotate_right", "rotate_up", "rotate_down"]:
        print(f"Executing mouse movement command: {command}")
        execute_mouse_movement(command)
    else:
       
        print(f"Executing keyboard command: {command}")
        
        
        if command == "go":
            pyautogui.press("w")
            print("Pressed 'w' key via PyAutoGUI")
        elif command == "enter":
            pyautogui.press("enter")
            print("Pressed 'enter' key via PyAutoGUI")
        elif command == "space":
            pyautogui.press("space")
            print("Pressed 'space' key via PyAutoGUI")
        else:
            print(f"Unknown command: {command}")
            return
        
        
        try:
            if command == "go":
                keyboard.press_and_release('w')
                print("Pressed 'w' key via keyboard module")
            elif command == "enter":
                keyboard.press_and_release('enter')
                print("Pressed 'enter' key via keyboard module")
            elif command == "space":
                keyboard.press_and_release('space')
                print("Pressed 'space' key via keyboard module")
        except Exception as e:
            print(f"Error with direct key press: {e}")
        
       
        try:
            if command == "go":
                vk_code = 0x57  # 'W' key
            elif command == "enter":
                vk_code = 0x0D  # Enter key
            elif command == "space":
                vk_code = 0x20  # Space key
            else:
                vk_code = None
                
            if vk_code:
                win32api.PostMessage(window_handle, win32con.WM_KEYDOWN, vk_code, 0)
                time.sleep(0.1)
                win32api.PostMessage(window_handle, win32con.WM_KEYUP, vk_code, 0)
                print(f"Sent key with VK code {vk_code} via Win32 API")
        except Exception as e:
            print(f"Error with Win32 key message: {e}")
    
    time.sleep(0.5)  # Pause to see the effect


def test_inputs(window_handle):
    print("\n----- TESTING INPUT METHODS -----")
    print("This will attempt to press W, Enter, Space and move the mouse in different directions.")
    if not window_handle:
        print("No window handle available to test with!")
        return
        
    focus_game_window(window_handle)
    time.sleep(1)
    
    # Test keyboard methods
    print("\nTesting PyAutoGUI for keyboard:")
    pyautogui.press('w')
    print("Pressed W with PyAutoGUI")
    time.sleep(1)
    
    print("\nTesting keyboard module:")
    keyboard.press_and_release('w')
    print("Pressed W with keyboard module")
    time.sleep(1)
    
    print("\nTesting Win32 API for keyboard:")
    vk_code = 0x57  # 'W' key
    win32api.PostMessage(window_handle, win32con.WM_KEYDOWN, vk_code, 0)
    time.sleep(0.1)
    win32api.PostMessage(window_handle, win32con.WM_KEYUP, vk_code, 0)
    print("Pressed W with Win32 API")
    time.sleep(1)
    
    
    print("\nTesting mouse movements:")
    execute_mouse_movement("rotate_left")
    time.sleep(1)
    execute_mouse_movement("rotate_right")
    time.sleep(1)
    execute_mouse_movement("rotate_up")
    time.sleep(1)
    execute_mouse_movement("rotate_down")
    time.sleep(1)
    
    print("----- INPUT TESTING COMPLETE -----\n")


def play_minecraft(window_title="Minecraft", debug_mode=False):
    print("Starting Minecraft AI controller... Press 'q' to quit.")
    print("This mode will analyze the game AND press keys / move the mouse!")
    
    
    minecraft_window = find_minecraft_window(window_title)
    if minecraft_window:
        window_name = win32gui.GetWindowText(minecraft_window)
        print(f"Found Minecraft window: {window_name}")
        
        
        if debug_mode:
            test_inputs(minecraft_window)
    else:
        print("No Minecraft window found. Will capture full screen instead.")
    
    action_log = []
    
    while True:
        if keyboard.is_pressed('q'):
            print("Stopping due to 'q' key press.")
            break
        
        
        try:
            if minecraft_window and win32gui.IsWindow(minecraft_window):
                pass  # Window still valid
            else:
                print("Window appears to be invalid. Searching again...")
                minecraft_window = find_minecraft_window(window_title)
        except Exception:
            print("Error checking window. Searching again...")
            minecraft_window = find_minecraft_window(window_title)
            
        
        img_base64, screenshot = capture_window_screenshot(minecraft_window)
        
        recommendation = get_minecraft_analysis(img_base64)
          
        if recommendation:
            timestamp = datetime.now().strftime("%H:%M:%S")
            action_log.append(f"{timestamp}: {recommendation}")
            
            
            execute_command(recommendation, minecraft_window)
            print(f"Executed action: {recommendation}")
        else:
            print("No valid recommendation received from AI.")
            
        
        if len(action_log) % 10 == 0:
            with open(os.path.join(SCREENSHOT_FOLDER, "action_log.txt"), "w") as f:
                f.write("\n".join(action_log))
                
        time.sleep(2)  # Reduced frequency to avoid API rate limits
        
    
    with open(os.path.join(SCREENSHOT_FOLDER, "action_log.txt"), "w") as f:
        f.write("\n".join(action_log))
    print(f"Action log saved to {os.path.join(SCREENSHOT_FOLDER, 'action_log.txt')}")

if __name__ == "__main__":
    
    game_window = input("Enter part of your Minecraft window title (default: 'Minecraft'): ") or "Minecraft"
    
    
    mode = input("Choose mode (1=Monitor only, 2=Play with AI controls, 3=Debug mode): ")
    
    print(f"Searching for Minecraft window containing '{game_window}' in title...")
    time.sleep(2)
    
    try:
        if mode == "3":
            # Debug mode first tests input methods then runs in play mode
            play_minecraft(game_window, debug_mode=True)
        elif mode == "2":
            play_minecraft(game_window)
        else:
            # Monitor mode only tests window focus
            minecraft_window = find_minecraft_window(game_window)
            if minecraft_window:
                window_name = win32gui.GetWindowText(minecraft_window)
                print(f"Found Minecraft window: {window_name}")
                print("Testing window focus...")
                focus_result = focus_game_window(minecraft_window)
                if focus_result:
                    print("Window focus test PASSED")
                else:
                    print("Window focus test FAILED - keys/mouse may not work")
                print("Running in monitor mode (no key presses or mouse movements)")
            else:
                print("No Minecraft window found - monitoring full screen")
    except KeyboardInterrupt:
        print("\nStopped by Ctrl+C.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        print("Minecraft AI assistant stopped.")
