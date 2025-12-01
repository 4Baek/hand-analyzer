// recommend.js
const RACKET_RECOMMEND_URL = "/recommend-rackets";

document.addEventListener("DOMContentLoaded", () => {
  // 파일/업로드 관련 엘리먼트
  const fileInput = document.getElementById("handImage");
  const uploadBtn = document.getElementById("uploadBtn");
  const fileNameEl = document.getElementById("fileName");
  const previewImg = document.getElementById("previewImage");
  const previewPlaceholder = document.getElementById("previewPlaceholder");
  const dropZone = document.getElementById("dropZone");

  // 상태/결과 영역
  const loadingEl = document.getElementById("loading");
  const errorBox = document.getElementById("errorBox");
  const handMetricsEl = document.getElementById("handMetrics");
  const racketListEl = document.getElementById("racketList");
  const stringRecommendationEl = document.getElementById("stringRecommendation");

  // 촬영 정보
  const captureDistanceInput = document.getElementById("captureDistanceInput");

  // 설문 요소
  const surveyLevel = document.getElementById("surveyLevel");
  const surveyPain = document.getElementById("surveyPain");
  const surveySwing = document.getElementById("surveySwing");
  const stylePower = document.getElementById("stylePower");
  const styleControl = document.getElementById("styleControl");
  const styleSpin = document.getElementById("styleSpin");
  const surveyStringType = document.getElementById("surveyStringType");

  const recommendBtn = document.getElementById("recommendBtn");

  // 상태
  let selectedFile = null;
  let lastHandMetrics = null;

  // -----------------------------
  // 공통 UI 유틸
  // -----------------------------

  function setLoading(isLoading) {
    if (loadingEl) {
      loadingEl.classList.toggle("hidden", !isLoading);
    }
    if (uploadBtn) uploadBtn.disabled = isLoading;
    if (recommendBtn) recommendBtn.disabled = isLoading;
  }

  function showError(message) {
    if (!errorBox) return;
    errorBox.textContent = message;
    errorBox.classList.remove("hidden");
  }

  function clearError() {
    if (!errorBox) return;
    errorBox.textContent = "";
    errorBox.classList.add("hidden");
  }

  function setFile(file) {
    selectedFile = file;

    if (!file) {
      if (fileNameEl) fileNameEl.textContent = "선택된 파일이 없습니다.";
      if (previewImg) previewImg.style.display = "none";
      if (previewPlaceholder) previewPlaceholder.style.display = "block";
      return;
    }

    if (fileNameEl) fileNameEl.textContent = file.name;

    const reader = new FileReader();
    reader.onload = (e) => {
      if (previewImg) {
        previewImg.src = e.target.result;
        previewImg.style.display = "block";
      }
      if (previewPlaceholder) {
        previewPlaceholder.style.display = "none";
      }
    };
    reader.readAsDataURL(file);
  }

  // -----------------------------
  // 설문 데이터 수집
  // -----------------------------

  function collectSurvey() {
    const styles = [];
    if (stylePower && stylePower.checked) styles.push("power");
    if (styleControl && styleControl.checked) styles.push("control");
    if (styleSpin && styleSpin.checked) styles.push("spin");

    return {
      level: surveyLevel ? surveyLevel.value || null : null,
      pain: surveyPain ? surveyPain.value || null : null,
      swing: surveySwing ? surveySwing.value || null : null,
      styles,
      stringTypePreference: surveyStringType
        ? surveyStringType.value || "auto"
        : "auto",
    };
  }

  // -----------------------------
  // 드래그 앤 드롭
  // -----------------------------

  if (dropZone) {
    ["dragenter", "dragover"].forEach((eventName) => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add("dragover");
      });
    });

    ["dragleave", "drop"].forEach((eventName) => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove("dragover");
      });
    });

    dropZone.addEventListener("drop", (e) => {
      const files = e.dataTransfer.files;
      if (files && files[0]) {
        setFile(files[0]);
      }
    });
  }

  // -----------------------------
  // 파일 선택
  // -----------------------------

  if (fileInput) {
    fileInput.addEventListener("change", () => {
      const file = fileInput.files[0];
      if (file) {
        setFile(file);
      }
    });
  }

  // -----------------------------
  // 손 이미지 업로드 & 분석 (손 분석만)
  // -----------------------------

  async function uploadHandImage() {
    if (!selectedFile) {
      showError("먼저 이미지를 선택해 주세요.");
      return;
    }

    clearError();
    setLoading(true);
    if (handMetricsEl) handMetricsEl.innerHTML = "";

    const formData = new FormData();
    formData.append("file", selectedFile);

    // 촬영 거리 (기본 30cm)
    let distanceCm = 30;
    if (captureDistanceInput) {
      const raw = captureDistanceInput.value;
      if (raw !== "" && !isNaN(raw)) {
        distanceCm = Number(raw);
      }
    }
    formData.append("captureDistance", distanceCm);

    try {
      const res = await fetch("/scan-hand", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const text = await res.text();
        showError(`손 분석 요청 실패 (${res.status}) : ${text}`);
        setLoading(false);
        return;
      }

      const metrics = await res.json();
      lastHandMetrics = metrics || null;
      renderHandMetrics(metrics);
    } catch (e) {
      showError(`손 분석 요청 중 오류가 발생했습니다: ${e}`);
    } finally {
      setLoading(false);
    }
  }

  if (uploadBtn) {
    uploadBtn.addEventListener("click", uploadHandImage);
  }

  // -----------------------------
  // 손 분석 결과 렌더링
  // -----------------------------

  function renderHandMetrics(metrics) {
    if (!metrics || !handMetricsEl) return;

    handMetricsEl.innerHTML = "";

    const {
      handLength,
      handWidth,
      fingerRatios,
      handLengthMm,
      handLengthCm,
      handWidthMm,
      handWidthCm,
      handSizeCategory,
    } = metrics;

    const items = [];

    // 상대 지수
    if (typeof handLength === "number") {
      items.push({
        label: "손 길이 지수",
        value: handLength.toFixed(0),
      });
    }

    if (typeof handWidth === "number") {
      items.push({
        label: "손 너비 지수",
        value: handWidth.toFixed(0),
      });
    }

    // mm/cm 추정값
    if (typeof handLengthMm === "number") {
      const cm =
        typeof handLengthCm === "number" ? handLengthCm : handLengthMm / 10.0;
      items.push({
        label: "손 길이 (추정값)",
        value: `${handLengthMm.toFixed(1)} mm / ${cm.toFixed(1)} cm`,
      });
    }

    if (typeof handWidthMm === "number") {
      const cm =
        typeof handWidthCm === "number" ? handWidthCm : handWidthMm / 10.0;
      items.push({
        label: "손 너비 (추정값)",
        value: `${handWidthMm.toFixed(1)} mm / ${cm.toFixed(1)} cm`,
      });
    }

    // 손가락 비율
    if (Array.isArray(fingerRatios) && fingerRatios.length > 0) {
      items.push({
        label: "손가락 비율 (검지/중지, 약지/중지)",
        value: fingerRatios.map((v) => v.toFixed(2)).join(" / "),
      });
    }

    // 손 크기 구분
    if (handSizeCategory) {
      let labelText = "";
      if (handSizeCategory === "SMALL") labelText = "작은 손";
      else if (handSizeCategory === "LARGE") labelText = "큰 손";
      else labelText = "보통 손";

      items.push({
        label: "손 크기 구분",
        value: labelText,
      });
    }

    if (items.length === 0) {
      handMetricsEl.innerHTML =
        '<span class="metric-label">표시할 손 분석 데이터가 없습니다.</span>';
      return;
    }

    for (const item of items) {
      const div = document.createElement("div");
      div.className = "metric-item";

      const label = document.createElement("div");
      label.className = "metric-label";
      label.textContent = item.label;

      const value = document.createElement("div");
      value.className = "metric-value";
      value.textContent = item.value;

      div.appendChild(label);
      div.appendChild(value);
      handMetricsEl.appendChild(div);
    }
  }

  // -----------------------------
  // 라켓 추천 요청
  // -----------------------------

  async function requestRacketRecommendation(metrics) {
    try {
      const survey = collectSurvey();
      const baseMetrics = metrics && typeof metrics === "object" ? metrics : {};

      // 백엔드 hand_service.recommend_rackets_from_metrics 와 계약:
      // - handLength, handWidth, fingerRatios 등 평탄한 메트릭 + survey 객체
      const payload = Object.assign({}, baseMetrics, { survey });

      const res = await fetch(RACKET_RECOMMEND_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const text = await res.text();
        showError(`라켓 추천 요청 실패 (${res.status}) : ${text}`);
        return;
      }

      const data = await res.json();

      // hand_service.py 반환 형식:
      // { rackets: [...], string: {...}, handProfile: {...} }
      if (data.rackets) {
        renderRacketList(data.rackets, racketListEl);
      } else {
        renderRacketList([], racketListEl);
      }

      if (data.string || data.stringRecommendation) {
        renderStringRecommendation(data.string || data.stringRecommendation);
      } else if (stringRecommendationEl) {
        stringRecommendationEl.innerHTML =
          '<span class="metric-label">스트링 추천 정보를 받지 못했습니다.</span>';
      }
    } catch (e) {
      showError(`라켓 추천 요청 중 오류가 발생했습니다: ${e}`);
    }
  }

  // -----------------------------
  // 라켓·스트링 추천 실행 버튼
  // -----------------------------

  async function handleRecommendClick() {
    clearError();
    setLoading(true);

    if (racketListEl) racketListEl.innerHTML = "";
    if (stringRecommendationEl) {
      stringRecommendationEl.innerHTML =
        '<span class="metric-label">스트링 추천을 준비 중입니다…</span>';
    }

    try {
      const metrics =
        lastHandMetrics && typeof lastHandMetrics === "object"
          ? lastHandMetrics
          : {};
      await requestRacketRecommendation(metrics);
    } finally {
      setLoading(false);
    }
  }

  if (recommendBtn) {
    recommendBtn.addEventListener("click", handleRecommendClick);
  }

  // -----------------------------
  // 스트링 추천 렌더링
  // -----------------------------

  function renderStringRecommendation(info) {
    if (!stringRecommendationEl) return;
    stringRecommendationEl.innerHTML = "";

    if (!info) {
      stringRecommendationEl.innerHTML =
        '<span class="metric-label">스트링 추천 정보를 받지 못했습니다.</span>';
      return;
    }

    const main = document.createElement("div");
    main.className = "string-main";

    const tensionTextParts = [];

    if (
      typeof info.tensionMainKg === "number" &&
      typeof info.tensionMainLbs === "number"
    ) {
      tensionTextParts.push(
        `${info.tensionMainKg.toFixed(1)}kg (${info.tensionMainLbs}lbs)`
      );
    }

    let label = info.stringLabel || "";
    if (!label && info.stringType) {
      if (info.stringType === "poly") label = "폴리 스트링";
      else if (info.stringType === "multi") label = "멀티필라멘트 스트링";
      else label = "기본 스트링";
    }

    main.textContent = tensionTextParts.length
      ? `${tensionTextParts.join(" / ")} · ${label}`
      : label || "스트링 추천 정보를 받지 못했습니다.";

    const reason = document.createElement("div");
    reason.className = "string-reason";
    if (info.reason) {
      reason.textContent = info.reason;
    }

    stringRecommendationEl.appendChild(main);
    if (info.reason) {
      stringRecommendationEl.appendChild(reason);
    }
  }

  // -----------------------------
  // 라켓 리스트 렌더링
  // -----------------------------

  function renderRacketList(data, container) {
    if (!container) return;

    container.innerHTML = "";

    const rackets = Array.isArray(data)
      ? data
      : Array.isArray(data?.rackets)
      ? data.rackets
      : [];

    if (rackets.length === 0) {
      container.textContent = "라켓 데이터가 없습니다.";
      return;
    }

    rackets.forEach((racket) => {
      const card = document.createElement("div");
      card.className = "racket-card";

      const header = document.createElement("div");
      header.className = "racket-header";

      const name = document.createElement("div");
      name.className = "racket-name";
      name.textContent =
        racket.name || racket.model || racket.racketName || "이름 없음";

      const score = document.createElement("div");
      score.className = "racket-score";
      if (typeof racket.score === "number") {
        // 100점은 소수점 없이, 나머지는 소수 첫째 자리까지
        if (Math.abs(racket.score - 100) < 0.05) {
          score.textContent = "적합도 100점";
        } else {
          score.textContent = `적합도 ${racket.score.toFixed(1)}점`;
        }
      } else if (
        typeof racket.power === "number" &&
        typeof racket.control === "number"
      ) {
        const s =
          typeof racket.spin === "number" ? racket.spin.toString() : "-";
        score.textContent = `P${racket.power}/C${racket.control}/S${s}`;
      } else {
        score.textContent = "";
      }

      header.appendChild(name);
      header.appendChild(score);
      card.appendChild(header);

      // ----- 스펙 태그: name / head_size_sq_in / string_pattern / unstrung_weight_g -----
      const tagsBox = document.createElement("div");
      tagsBox.className = "racket-tags";

      const specName =
        racket.name || racket.model || racket.racketName || null;

      const headSize =
        typeof racket.headSize === "number"
          ? racket.headSize
          : typeof racket.head_size_sq_in === "number"
          ? racket.head_size_sq_in
          : null;

      const stringPattern =
        racket.stringPattern || racket.string_pattern || null;

      const unstrungWeight =
        typeof racket.unstrungWeight === "number"
          ? racket.unstrungWeight
          : typeof racket.unstrung_weight_g === "number"
          ? racket.unstrung_weight_g
          : typeof racket.weight === "number"
          ? racket.weight
          : null;

      function appendTag(text) {
        if (!text) return;
        const tag = document.createElement("span");
        tag.className = "racket-tag";
        tag.textContent = text;
        tagsBox.appendChild(tag);
      }

      // DB 컬럼 기준으로 태그 구성
      appendTag(specName);
      if (headSize !== null) appendTag(`${headSize} sq.in`);
      appendTag(stringPattern);
      if (unstrungWeight !== null) appendTag(`${unstrungWeight} g`);

      // 백엔드에서 별도 tags 배열을 내려주는 경우도 함께 표시
      if (Array.isArray(racket.tags)) {
        racket.tags.forEach((t) => appendTag(t));
      }

      if (tagsBox.childElementCount > 0) {
        card.appendChild(tagsBox);
      }

      // 추천 이유 영역
      const reasonBox = document.createElement("div");
      reasonBox.className = "racket-reason";
      if (racket.reason) {
        reasonBox.textContent = racket.reason;
      } else {
        // 기본 문구만, '(추측입니다)' 제거
        reasonBox.textContent =
          "손 크기와 플레이 스타일을 종합해 추천 목록에 포함된 라켓입니다.";
      }
      card.appendChild(reasonBox);

      container.appendChild(card);
    });
  }
});
