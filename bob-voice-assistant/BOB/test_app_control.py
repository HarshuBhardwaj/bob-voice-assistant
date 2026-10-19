
from core.app_control import AppControl

apps = AppControl()

# Test opening Chrome
apps.launch_app("chrome")

# Test opening Calculator
apps.launch_app("calculator")

# Test closing Calculator
#apps.close_app("calculator")
