
from core.file_control import FileControl

fc = FileControl()

tests = [
    "heart dot csv",
    "heart.csv",
    "hello dot png",
    "my file dot pdf",
    "data under score final dot csv",
]

for name in tests:
    print(f"{name}  ->  {fc.normalize_filename(name)}")
