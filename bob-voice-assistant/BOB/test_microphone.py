
import speech_recognition as sr

recognizer = sr.Recognizer()

print("Available microphones:")
for index, name in enumerate(sr.Microphone.list_microphone_names()):
    print(f"{index}: {name}")

try:
    with sr.Microphone() as source:
        print("\nPlease stay quiet for 2 seconds...")
        recognizer.adjust_for_ambient_noise(source, duration=2)

        print("Energy threshold:", recognizer.energy_threshold)
        print("\nSpeak normally now...")
        audio = recognizer.listen(
            source,
            timeout=10,
            phrase_time_limit=6
        )

    print("Audio captured. Recognizing speech...")

    text = recognizer.recognize_google(
        audio,
        language="en-IN"
    )

    print("Recognized:", text)

except sr.WaitTimeoutError:
    print("No speech detected. Check microphone input and volume.")

except sr.UnknownValueError:
    print("Audio captured, but speech could not be understood.")

except sr.RequestError as error:
    print("Speech service/network error:", error)

except Exception as error:
    print("Microphone test failed:", repr(error))
