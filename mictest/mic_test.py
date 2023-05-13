import speech_recognition as sr

# Path to the audio file
AUDIO_FILE_PATH = "./mictest/audio.wav"

def record_audio():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Say your words for printing")
        recognizer.pause_threshold = 1
        audio = recognizer.listen(source, phrase_time_limit=5, timeout=None)
    return audio
    
    
def main():
    print("Starting main function")

    filename = "./audio3.wav"

     audio = record_audio()
     with open(filename, "wb") as audio_file:
     	audio_file.write(audio.get_wav_data())
     print("Archivo de audio guardado en:", filename)
     with open(filename, "wb") as audio_file:
     	audio_file.write(audio.get_wav_data())
            
 
main()
