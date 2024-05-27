from flask import Flask, render_template, request, redirect, url_for, Response, jsonify
from ultralytics import YOLO
import cv2
import os
from PIL import Image
import datetime
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO
from function import download_zip
import threading

app = Flask(__name__)
app.static_folder = 'static'

# Load the YOLOv8 model
model = YOLO(r'best.pt')

camera = None  #  camera globally
lock = threading.Lock()  # Lock to handle camera access
is_running = False  # Flag to control the camera

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/imgpred', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'images[]' not in request.files:
            message = {
                'error': "No image uploaded!",
                'success': False
            }
            return jsonify(message)
        if request.files['images[]'].filename == '':
            message = {
                'error': "No image selected!",
                'success': False
            }
            return jsonify(message)
        
        # Apple Counting
        n_images = 0
        n_apple = 0
        fa_apple = 0
        sa_apple = 0

        # for save img_path
        img_path = "static/imgpred/"
        img_results = []

        files = request.files.getlist('images[]')

        for file in files:
            if file:
                n_images += 1

                # Save the uploaded image to a temporary location
                filename = file.filename
                image_path = img_path + filename
                file.save(image_path)

                # Run inference on the uploaded image
                results = model(image_path)  # results list

                # make a image filename
                now =  datetime.datetime.now()
                result_image = filename + now.strftime("%Y%m%d_%H%M%S") + ".jpg"

                # Visualize the results
                for i, r in enumerate(results):
                    #Counting Section
                    boxes = r.boxes  # Boxes object for bounding box outputs
                    for cls in boxes.cls:
                        n_apple += 1
                        if(cls == 0):
                            fa_apple += 1
                        else:
                            sa_apple += 1
                    
                    # Plot results image
                    im_bgr = r.plot()  # BGR-order numpy array
                    im_rgb = Image.fromarray(im_bgr[..., ::-1])  # RGB-order PIL image

                    # Save the result image
                    result_image_path = img_path + result_image
                    img_results.append(result_image_path)
                    im_rgb.save(result_image_path)

                # Remove the uploaded image
                os.remove(image_path)

        # Membuat plot
        # Generate random data for two categories
        category1 = np.random.normal(loc=0, scale=1, size=1000)
        category2 = np.random.normal(loc=3, scale=1.5, size=1000)

        # Create histogram for category 1
        # fig, ax = plt.subplots()
        # ax.hist(category1, bins=30, color='blue', alpha=0.5, label='Category 1')

        # # Create histogram for category 2
        # ax.hist(category2, bins=30, color='red', alpha=0.5, label='Category 2')

        # ax.set_title('Histogram with Two Categories')
        # ax.set_xlabel('Value')
        # ax.set_ylabel('Frequency')
        # ax.legend()

        # # Menyimpan plot ke dalam string base64
        # img = BytesIO()
        # fig.savefig(img, format='png')
        # img.seek(0)
        plot_data = 0
        # plot_data = base64.b64encode(img.getvalue()).decode()
        # plt.close(fig)

        # Render the HTML template with the result image path
        # return render_template('index.html', plot_data=plot_data, 
        # img_results=img_results, image_path=result_image_path, n_apple=n_apple, n_images=n_images, fa_apple=fa_apple, sa_apple=sa_apple)
        message = {
                'success': True,
                'img_results': img_results,
                'n_apple': n_apple,
                'n_images': n_images,
                'fa_apple': fa_apple,
                'sa_apple': sa_apple
            }
        return jsonify(message)
    else:
        return "get"
        return redirect('/')
    
@app.route('/vidpred', methods=['GET', 'POST'])
def upload_video():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            return redirect(request.url)
        
        if file:
            video_path = os.path.join('static', 'uploaded_video.mp4')
            file.save(video_path)
            
            return redirect(url_for('video_feed', video_path=video_path))
    
    return render_template('index.html')

def generate_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    
    while cap.isOpened():
        success, frame = cap.read()

        if success:
            results = model(frame)
            annotated_frame = results[0].plot()
            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            break

    cap.release()

@app.route('/video_feed')
def video_feed():
    video_path = request.args.get('video_path', None)
    
    if video_path:
        return Response(generate_frames(video_path), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return 'Error: No video file provided.'
    
@app.route('/predict_download', methods=['POST'])
def predict_download():
    file_list = request.form.getlist('img_results[]')

    zs = []
    for file in file_list:
        zs.append(file)

    return download_zip(zs)

@app.route('/live_feed')
def live_feed():
    return Response(generate_live_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_live_frames():
    cap = cv2.VideoCapture(1)  # 0 represents the default webcam

    while True:
        success, frame = cap.read()

        if success:
            # Perform prediction on the frame using your YOLO model
            results = model(frame)
            annotated_frame = results[0].plot()

            # Convert the annotated frame to JPEG format
            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            frame_bytes = buffer.tobytes()

            # Yield the frame bytes as part of the response
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            break

    cap.release()

# @app.route('/start_camera', methods=['POST'])
# def start_camera():
#     global camera, is_running
#     with lock:
#         if camera is None or not camera.isOpened():
#             camera = cv2.VideoCapture(0)
#         is_running = True
#     return '', 204

if __name__ == "__main__":
    #app.run(debug=True)
    app.run(debug=False, port=5000, host='0.0.0.0', threaded = True)