from flask import Flask, render_template, request, redirect, url_for, Response, jsonify
from ultralytics import YOLO
import cv2
import os
from PIL import Image
import datetime
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

# for image detection
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
        message = {
                'success': False,
                'error': "You don't have access with this page!"
            }
        return jsonify(message)
    
@app.route('/predict_download', methods=['POST'])
def predict_download():
    file_list = request.form.getlist('img_results[]')

    zs = []
    for file in file_list:
        zs.append(file)

    return download_zip(zs)

# for video detection
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

# for realtime detection
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

#fungsi deteksi camera real time 
def gen_frames():
    global camera, is_running
    while is_running:
        with lock:
            if camera is None or not camera.isOpened():
                continue
            success, frame = camera.read()
        if not success:
            continue
        else:
            # Perform object detection
            results = model(frame)
            detections = results[0].boxes  # Access the detections

            # Draw bounding boxes on the frame
            for box in detections:  # Iterate through detections
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # Get bounding box coordinates
                conf = box.conf[0]  # Confidence score
                cls = int(box.cls[0])  # Class label
                label = f'{model.names[cls]} {conf:.2f}'

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            frame = buffer.tobytes()

            # Yield the output frame in byte format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/start_camera', methods=['POST'])
def start_camera():
    global camera, is_running
    with lock:
        if camera is None or not camera.isOpened():
            camera = cv2.VideoCapture(0)
        is_running = True
    return '', 204

@app.route('/stop_camera', methods=['POST'])
def stop_camera():
    global camera, is_running
    with lock:
        if camera is not None and camera.isOpened():
            camera.release()
            camera = None
        is_running = False
    return '', 204

if __name__ == "__main__":
    #app.run(debug=True)
    app.run(debug=False, port=5000, host='0.0.0.0', threaded = True)