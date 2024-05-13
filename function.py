from zipfile import ZipFile
from flask import send_file

# Fungsi untuk mengunduh file ZIP
def download_zip(files_to_zip):
    try:
        # Buat objek ZipFile
        zip_file = ZipFile('storage/predict_apple.zip', 'w')

        # Tambahkan setiap file ke dalam ZIP
        for file in files_to_zip:
            zip_file.write(file)

        # Tutup objek ZipFile
        zip_file.close()

        # Kirim file ZIP sebagai respons
        return send_file('storage/predict_apple.zip', as_attachment=True)

    except Exception as e:
        return str(e)