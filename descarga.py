import firebase_admin
from firebase_admin import credentials, storage

# Initialize the app with a service account
cred = credentials.Certificate('/home/orangepi/KlipperScreen/panels/credentials.json')  # replace this with the path to your service account key
default_app = firebase_admin.initialize_app(cred, {
    'storageBucket': 'test-klipperscreen.appspot.com'
})

# Get a reference to the storage service
bucket = storage.bucket()

# Create a blob with the file name
blob = bucket.blob('gcode/cube.gcode')

# Download the file to a destination
with open('/home/orangepi/printer_data/gcodes/cube.gcode', 'wb') as file_obj:
    blob.download_to_file(file_obj)

# Delete the blob
blob.delete()

