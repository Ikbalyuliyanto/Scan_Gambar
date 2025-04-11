from flask import Flask, request, jsonify
from paddleocr import PaddleOCR
import cv2
import numpy as np

app = Flask(__name__)
ocr = PaddleOCR(use_angle_cls=True, lang='en')

@app.route('/scan', methods=['POST'])
def scan():
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No image uploaded'}), 400

    file = request.files['image']
    img_array = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    result = ocr.ocr(img, cls=True)
    extracted = [line[1][0] for line in result[0]]

    return jsonify({'success': True, 'extractedText': extracted})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)