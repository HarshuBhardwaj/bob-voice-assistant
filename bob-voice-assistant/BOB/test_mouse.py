
import time
from core.universal_control import UniversalControl

control = UniversalControl()

print("Screen size:", control.get_screen_size())

input("Press Enter to start mouse movement test...")

print("Mouse will move to the center in 3 seconds.")
time.sleep(3)

width, height = control.get_screen_size()
control.move_mouse(width // 2, height // 2)

print("Mouse movement command sent.")
time.sleep(1)

input("Press Enter to test a mouse click...")

control.click()
print("Mouse click command sent.")

