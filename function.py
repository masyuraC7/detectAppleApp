import zipfile
from flask import send_file
import os

# Fungsi untuk mengunduh file ZIP
def download_zip(files_to_zip):
    try:
        with zipfile.ZipFile("static/predict/predict_apple.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files_to_zip:
                # Menentukan nama file di dalam folder target di ZIP
                file_name = os.path.basename(file_path)
                custom_path = os.path.join("predict", file_name)
                zipf.write(file_path, arcname=custom_path)

        # Kirim file ZIP sebagai respons
        return send_file('static/predict/predict_apple.zip', as_attachment=True)

    except Exception as e:
        return str(e)