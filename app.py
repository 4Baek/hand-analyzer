from flask import Flask, request, jsonify
from hand_utils import analyze_hand
import os

app = Flask(__name__)

@app.route('/scan-hand', methods=['POST'])
def scan_hand():
    if 'file' not in request.files:
        return jsonify({'error': '이미지 파일이 필요합니다'}), 400

    file = request.files['file']
    file_path = os.path.join('temp.jpg')
    file.save(file_path)

    result = analyze_hand(file_path)
    if result is None:
        return jsonify({'error': '손 인식 실패'}), 400

    return jsonify(result)

if __name__ == '__main__':
    app.run(port=5000)
