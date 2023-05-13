import os
import time
import threading
import firebase_admin
import openai
import speech_recognition as sr
import gi
import matplotlib.pyplot as plt
from firebase_admin import credentials, db, storage
from stl import mesh
from gi.repository import Gtk
from contextlib import contextmanager
from ks_includes.screen_panel import ScreenPanel
import wave
from gi.repository import Gtk, GLib
import cairo
from io import BytesIO
from gi.repository import GdkPixbuf










def create_panel(*args, **kwargs):
    return VoiceToSTLPanel(*args, **kwargs)

# Replace with the path to the Firebase JSON credentials file
FIREBASE_CREDENTIALS_PATH = "/home/orangepi/KlipperScreen/panels/credentials.json"




# Path to the audio file
AUDIO_FILE_PATH = "./audio.wav"

# Path to the downloaded STL file
STL_FILE_PATH = "./cubo.stl"

# Initialize Firebase

firebase_admin.initialize_app(
    credentials.Certificate(FIREBASE_CREDENTIALS_PATH),
    {
        "storageBucket": "gs://test-klipperscreen.appspot.com",
        "databaseURL": "https://test-klipperscreen-default-rtdb.europe-west1.firebasedatabase.app/",
    },
)

gi.require_version("Gtk", "3.0")


class VoiceToSTLPanel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title)
        # Set up UI elements
        self.setup_ui()

        # Set up plotter and cancel request flag
        
        self.cancel_requested = False

    def setup_ui(self):
        main_container = Gtk.Grid()
        main_container.set_column_spacing(12)
        main_container.set_row_spacing(6)
        main_container.set_margin_start(12)
        main_container.set_margin_end(12)
        main_container.set_margin_top(12)
        main_container.set_margin_bottom(12)
        self.content.add(main_container)

        execute_button = self.create_button("", self.execute_my_script)
        execute_button.set_size_request(64, 64)
        execute_button.set_always_show_image(True)  # Mostrar imagen todo el tiempo
        execute_button.set_image_position(Gtk.PositionType.TOP)  # Posición de la imagen
        main_container.attach(execute_button, 0, 0, 1, 1)

       




        # Etiqueta de estado
        self.status_label = Gtk.Label()
        main_container.attach(self.status_label, 0, 2, 3, 1)

        # Etiqueta de transcripción
        self.transcription_label = Gtk.Label()
        self.transcription_label.set_line_wrap(True)  # Habilitar ajuste de línea
        main_container.attach(self.transcription_label, 0, 3, 3, 1)

    

    # Método adicional para manejar el evento del botón de configuración
    def on_settings_button_clicked(self, widget):
        print("Configuración")
        self.show_settings_dialog()

    def show_settings_dialog(self):
        dialog = Gtk.Dialog(title="Configuración", transient_for=self.screen.window, flags=0)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)

        content_area = dialog.get_content_area()
        content_area.set_margin_start(6)
        content_area.set_margin_end(6)
        content_area.set_margin_top(6)
        content_area.set_margin_bottom(6)

        # Aquí puedes agregar los elementos para la configuración del programa
        settings_label = Gtk.Label(label="Añade aquí tus elementos de configuración.")
        content_area.add(settings_label)

        dialog.show_all()

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            print("Aplicar cambios de configuración")
            # Aquí puedes aplicar los cambios de configuración según los valores en los widgets de la ventana de configuración
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancelar configuración")

        dialog.destroy()

    def create_button(self, label, callback):
         button = self._gtk.Button(label=label)
         button.connect("clicked", callback)
         return button
        
    def update_transcription_label(self, text):
        self.transcription_label.set_text(text)

    def on_cancel_button_clicked(self, widget):
        print("Cancel/stop the process")
        self.cancel_requested = True
        stop_recognition_and_servers()

    def update_progress_bar(self, fraction):
        GLib.idle_add(self.progress_bar.set_fraction, fraction)


    def execute_my_script(self, widget):
        print("Ejecutando el script...")
        self.update_status_label("Ejecutando el script...")

        

        # Grabar audio y procesar
        thread = threading.Thread(target=main, args=(self,))
        thread.start()

        # Detener la animación y volver al icono original después de grabar el audio
        def stop_animation():
            self.execute_button.get_image().set_from_icon_name("microphone-sensitivity-high-symbolic", Gtk.IconSize.BUTTON)

        GLib.timeout_add(5000, stop_animation)  # Cambia 5000 por la duración de la animación en milisegundos



    def update_status_label(self, text):
        if text == "Ejecutando el script...":
            GLib.idle_add(self.status_label.set_text, text)
        else:
            pass

        

    def load_and_show(self, stl_path):
        # Cargar el archivo STL
        stl_mesh = mesh.Mesh.from_file(stl_path)

        # Crear una figura y un eje 3D
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")

        # Renderizar el modelo 3D
        ax.add_collection3d(plt.PolyCollection(stl_mesh.vectors, facecolors="k"))

        # Escalar y centrar el modelo 3D
        scale = stl_mesh.points.flatten()
        ax.auto_scale_xyz(scale, scale, scale)

        # Mostrar la figura
        plt.show()


    def transcribe_audio_to_text(self, filename):
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(filename) as source:
                audio = recognizer.record(source)
            return recognizer.recognize_google(audio)
        except Exception as e:
            print(f"Error en la transcripción: {e}")
            return None
        
    

        

def record_audio():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Say your words for printing")
        recognizer.pause_threshold = 1
        audio = recognizer.listen(source, phrase_time_limit=5, timeout=None)
    return audio





def stop_recognition_and_servers():
        os.system("killall -9 arecord")
        os.system("killall -9 jackd")
        os.system("killall -9 pulseaudio")



def check_cancel(panel):
    if panel.cancel_requested:
        panel.update_status_label("Proceso cancelado.")
        return True
    return False


def save_text_to_firebase(text):
    ref = db.reference("transcriptions")
    transcription_ref = ref.push()
    transcription_ref.set({"text": text, "status": "waiting"})
    return transcription_ref


def wait_for_server_processing(transcription_ref, panel):
    while not check_cancel(panel):
        status = transcription_ref.get()["status"]
        if status == "done":
            break
        time.sleep(1)


def download_stl_file(stl_path, transcription_ref_key):
    stl_blob = storage.bucket().blob(f"stl/{transcription_ref_key}.stl")
    stl_blob.download_to_filename(stl_path)




def main(panel):
    print("Starting main function")
    stl_saved = False

    filename = "./audio3.wav"

    while not stl_saved:

        # Record audio and save it to a file
        audio = record_audio()
        with open(filename, "wb") as audio_file:
            audio_file.write(audio.get_wav_data())
        print("Archivo de audio guardado en:", filename)

        with open(filename, "wb") as audio_file:
            audio_file.write(audio.get_wav_data())

        # Transcribe audio to text
        text = panel.transcribe_audio_to_text(filename) or None

        if text:
            panel.update_status_label(f"Dijiste: {text}")

            panel.update_status_label("Guardando texto en Firebase...")
            if check_cancel(panel):
                break

            ref = db.reference('transcriptions')
            transcription_ref = ref.push()
            transcription_ref.set({'text': text, 'status': 'waiting'})

            time.sleep(10)
            os.system("python3 /home/orangepi/KlipperScreen/descarga.py")

            # Wait for server processing
            panel.update_status_label("Esperando a que el servidor procese el texto...")
            if check_cancel(panel):
                break
            while True:
                if check_cancel(panel):
                    break
                status = transcription_ref.get()['status']
                if status == 'done':
                    break
                time.sleep(1)

if __name__ == "__main__":
    main()

