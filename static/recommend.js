document.getElementById('uploadForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    const imageInput = document.getElementById('image');
    const resultDiv = document.getElementById('result');
  
    if (!imageInput.files.length) {
      resultDiv.textContent = '실패: 이미지 파일이 필요합니다';
      return;
    }
  
    const formData = new FormData();
    formData.append('image', imageInput.files[0]);
  
    try {
      const scanRes = await fetch('http://localhost:5000/scan-hand', {
        method: 'POST',
        body: formData
      });
  
      const rackets = await scanRes.json();
      console.log("📨 추천 결과:", rackets);
  
      if (!scanRes.ok) {
        resultDiv.textContent = `추천 요청 실패: ${rackets.message || '오류 발생'}`;
        return;
      }
  
      if (!Array.isArray(rackets) || rackets.length === 0) {
        resultDiv.textContent = '추천 결과가 없습니다.';
        return;
      }
  
      resultDiv.innerHTML = '<h3>추천된 라켓:</h3><ul>' +
        rackets.map(r => `<li>${r.name} (${r.type})</li>`).join('') +
        '</ul>';
    } catch (error) {
      console.error('❌ 요청 중 오류:', error);
      resultDiv.textContent = '서버 통신 오류';
    }
  });
  