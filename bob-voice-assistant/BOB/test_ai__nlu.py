
from core.nlu import NaturalLanguageUnderstanding

print("Starting Groq NLU test...", flush=True)

nlu = NaturalLanguageUnderstanding()

commands = [
    "mere downloads dikhao",
    "ab documents ko kholo",
    "go back",
    "YouTube par Arijit Singh ke songs dhundo",
]

for text in commands:
    print(f"\nInput: {text}", flush=True)

    try:
        result = nlu.normalize(text)
        print(f"Output: {result}", flush=True)
    except RuntimeError as error:
        print(f"FAILED: {error}", flush=True)
