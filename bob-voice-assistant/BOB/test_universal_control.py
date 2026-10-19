from core.universal_control import UniversalControl

control = UniversalControl()

print("Screen:", control.get_screen_size())

input("Notes mein click karo, phir yahan Enter dabao...")

print("5 seconds mein typing shuru hogi...")
import time
time.sleep(5)

print("Typing test:", control.type_text("Hello from BOB"))