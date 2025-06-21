from flask import Flask, request, jsonify, render_template
from hand_utils import analyze_hand
import os
import requests

app = Flask(__name__)

# HTML 페이지 렌더링
@app.route('/')
def index():
    return render_template("index.html")

# 이미지 업로드 및 손 분석 → Java 서버로 전달
@app.route('/scan-hand', methods=['POST'])
def scan_hand():
    if 'image' not in request.files:
        return jsonify({'error': '이미지 파일이 필요합니다'}), 400

    file = request.files['image']
    file_path = os.path.join('temp.jpg')
    file.save(file_path)

    result = analyze_hand(file_path)
    if not result:
        return jsonify({'error': '손 인식 실패'}), 400
    if result is None:
        return jsonify({'error': '손 인식 실패'}), 400
    # 결과가 리스트인 경우 첫 번째 항목만 사용
    if isinstance(result, list):
        result = result[0]

    java_url = 'http://localhost:8080/recommend'
    try:
        print("✅ Java로 전달할 JSON:", result)
        java_response = requests.post(java_url, json=[result], timeout=5)
        print("📨 Java 응답 코드:", java_response.status_code)
        print("📨 Java 응답 본문:", java_response.text)
        java_response.raise_for_status()
        return jsonify(java_response.json())
    except requests.exceptions.RequestException as e:
        print("[Java 연동 오류]", e)
        return jsonify({'error': 'Java 서버 통신 실패'}), 500

if __name__ == '__main__':
    app.run(port=5000)
