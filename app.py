from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import io
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
from PIL.ExifTags import TAGS
from google.cloud import storage

app = Flask(__name__)

bucket_name = 'project-2-images'
# Function to generate a unique filename based on timestamp
def generate_unique_filename(filename):
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{current_time}_{filename}"

@app.route('/')
def home():
    # Initialize the Google Cloud Storage client
    storage_client = storage.Client()

    # Get a list of all objects (images) in the GCS bucket
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs()

    # Extract the filenames from the blobs
    image_files = [blob.name for blob in blobs]

    return render_template('home.html', image_files=image_files)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)

        if file:
            filename = generate_unique_filename(secure_filename(file.filename))
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(filename)
            blob.upload_from_file(file)
            exif_data = {}
            try:
                with Image.open(file) as img:
                    if hasattr(img, '_getexif'):
                        exif_info = img._getexif()
                        if exif_info is not None:
                            # Specify the EXIF tags you want to extract
                            desired_tags = {
                                'Make': TAGS.get('Make', 'Make'),
                                'Model': TAGS.get('Model', 'Model'),
                                'ISO': TAGS.get('ISOSpeedRatings', 'ISO'),
                                # Add more tags as needed
                            }
                            for tag, value in exif_info.items():
                                tag_name = TAGS.get(tag, tag)
                                if tag_name in desired_tags:
                                    exif_data[desired_tags[tag_name]] = value
            except Exception as e:
                print(f"Error extracting EXIF data: {str(e)}")
            
            metadata = {
                'size': str(blob.size)+" Bytes" ,  # Convert the size to a string
                'directory': bucket_name+"/"+filename,
                'name': filename,
                **exif_data
            }

            blob.metadata = metadata

            # Update the object's metadata in the bucket
            blob.patch()

            return redirect(url_for('home'))
    return render_template('upload.html')

@app.route('/image/<filename>')
def image(filename):
    storage_client = storage.Client()
    gcs_url = f'https://storage.googleapis.com/{bucket_name}/{filename}'
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.get_blob(filename)


    if blob.exists():
        image_metadata = blob.metadata
    else:
        image_metadata['Status'] = 'Image not found in GCS bucket'

    return render_template('image.html', filename=filename, gcs_url=gcs_url, image_metadata=image_metadata)

@app.route('/download/<filename>')
def download(filename):
    # Construct the GCS URL for the file to be downloaded
    gcs_url = f'https://storage.googleapis.com/{bucket_name}/{filename}'

    # Redirect the user to the GCS URL for download
    return redirect(gcs_url)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

