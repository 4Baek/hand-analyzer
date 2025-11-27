// recommend.js

const RACKET_RECOMMEND_URL = "/recommend-rackets";

document.addEventListener("DOMContentLoaded", () => {
  const fileInput = document.getElementById("handImage");
  const uploadBtn = document.getElementById("uploadBtn");
  const fileNameEl = document.getElementById("fileName");
  const previewImg = document.getElementById("previewImage");
  const previewPlaceholder = document.getElementById("previewPlaceholder");
  const dropZone = document.getElementById("dropZone");

  const loadingEl = document.getElementById("loading");
  const errorBox = document.getElementById("errorBox");
  const handMetricsEl = document.getElementById("handMetrics");
  const racketListEl = document.getElementById("racketList");
  const stringRecommendationEl = document.getElementById("stringRecommendation");

  // DB 관리 관련 요소
  const btnResetDb = document.getElementById("btnResetDb");
  const btnLoadAllRackets = document.getElementById("btnLoadAllRackets");
  const adminStatusEl = document.getElementById("adminStatus");
  const adminRacketListEl = document.getElementById("adminRacketList");

  const adminNewName = document.getElementById("adminNewName");
  const adminNewBrand = document.getElementById("adminNewBrand");
  const adminNewPower = document.getElementById("adminNewPower");
  const adminNewControl = document.getElementById("adminNewControl");
  const adminNewSpin = document.getElementById("adminNewSpin");
  const adminNewWeight = document.getElementById("adminNewWeight");
  const adminNewTags = document.getElementById("adminNewTags");
  const btnAddRacket = document.getElementById("btnAddRacket");

  // 설문 요소
  const surveyLevel = document.getElementById("surveyLevel");
  const surveyPain = document.getElementById("surveyPain");
  const surveySwing = document.getElementById("surveySwing");
  const stylePower = document.getElementById("stylePower");
  const styleControl = document.getElementById("styleControl");
  const styleSpin = document.getElementById("styleSpin");
  const surveyStringType = document.getElementById("surveyStringType");

  let selectedFile = null;

  // -----------------------------
  // 공통 UI 유틸
  // -----------------------------

  function setLoading(isLoading) {
    if (loadingEl) {
      loadingEl.classList.toggle("hidden", !isLoading);
    }
    if (uploadBtn) {
      uploadBtn.disabled = isLoading;
    }
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
  // 손 이미지 업로드 & 분석
  // -----------------------------

  async function uploadHandImage() {
    if (!selectedFile) {
      showError("먼저 이미지를 선택해 주세요.");
      return;
    }

    clearError();
    setLoading(true);
    if (handMetricsEl) handMetricsEl.innerHTML = "";
    if (racketListEl) racketListEl.innerHTML = "";
    if (stringRecommendationEl) {
      stringRecommendationEl.innerHTML =
        '<span class="metric-label">스트링 추천을 준비 중입니다…</span>';
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

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
      renderHandMetrics(metrics);
      await requestRacketRecommendation(metrics);
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

    const { handLength, handWidth, fingerRatios } = metrics;

    const items = [];

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

    if (Array.isArray(fingerRatios)) {
      items.push({
        label: "손가락 비율 (검지/중지, 약지/중지)",
        value: fingerRatios.map((v) => v.toFixed(2)).join(" / "),
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
      const payload = Object.assign({}, metrics, { survey });

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
      renderRacketList(data, racketListEl); // 메인 결과에는 삭제 버튼 X

      if (data && (data.string || data.stringRecommendation)) {
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
  // 라켓 리스트 렌더링 (공통)
  // options: { showDelete: boolean, onDelete: (id) => void }
  // -----------------------------

  function renderRacketList(data, container, options = {}) {
    if (!container) return;

    const { showDelete = false, onDelete = null } = options;

    container.innerHTML = "";

    if (!data) {
      container.textContent = "라켓 데이터가 없습니다.";
      return;
    }

    const rackets = Array.isArray(data.rackets) ? data.rackets : data;

    if (!Array.isArray(rackets) || rackets.length === 0) {
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
        score.textContent = `적합도 ${racket.score.toFixed(1)}점`;
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

      // 관리 화면에서만 삭제 버튼 추가
      if (showDelete && typeof racket.id === "number" && onDelete) {
        const delBtn = document.createElement("button");
        delBtn.className =
          "button button-secondary button-small button-danger";
        delBtn.textContent = "삭제";
        delBtn.addEventListener("click", () => onDelete(racket.id));
        header.appendChild(delBtn);
      }

      card.appendChild(header);

      const tagsBox = document.createElement("div");
      tagsBox.className = "racket-tags";

      const brand = racket.brand || racket.manufacturer;
      if (brand) {
        const tag = document.createElement("span");
        tag.className = "racket-tag";
        tag.textContent = brand;
        tagsBox.appendChild(tag);
      }

      if (Array.isArray(racket.tags)) {
        racket.tags.forEach((t) => {
          const tag = document.createElement("span");
          tag.className = "racket-tag";
          tag.textContent = t;
          tagsBox.appendChild(tag);
        });
      }

      if (tagsBox.childElementCount > 0) {
        card.appendChild(tagsBox);
      }

      container.appendChild(card);
    });
  }

  // -----------------------------
  // DB 관리 상태 표시
  // -----------------------------

  function setAdminStatus(message, isError = false) {
    if (!adminStatusEl) return;
    adminStatusEl.textContent = message;
    adminStatusEl.classList.toggle("admin-status-error", !!isError);
  }

  // -----------------------------
  // DB 초기화 버튼
  // -----------------------------

  async function handleResetDb() {
    if (!confirm("정말로 DB를 초기화하고 샘플 데이터로 다시 채울까요?")) {
      return;
    }

    try {
      setAdminStatus("DB 초기화 요청 중...");
      const res = await fetch("/admin/reset-db", {
        method: "POST",
      });

      if (!res.ok) {
        const text = await res.text();
        setAdminStatus(`DB 초기화 실패 (${res.status}) : ${text}`, true);
        return;
      }

      const data = await res.json();
      setAdminStatus(data.message || "DB가 초기화되었습니다.");
      await handleLoadAllRackets();
    } catch (e) {
      setAdminStatus(`DB 초기화 에러: ${e}`, true);
    }
  }

  if (btnResetDb) {
    btnResetDb.addEventListener("click", handleResetDb);
  }

  // -----------------------------
  // DB 라켓 전체 조회 버튼
  // -----------------------------

  async function handleLoadAllRackets() {
    try {
      setAdminStatus("DB 라켓 목록 조회 중...");
      const res = await fetch("/admin/rackets");

      if (!res.ok) {
        const text = await res.text();
        setAdminStatus(`DB 라켓 조회 실패 (${res.status}) : ${text}`, true);
        return;
      }

      const data = await res.json();
      setAdminStatus("DB 라켓 목록 조회 완료.");
      renderRacketList(data, adminRacketListEl, {
        showDelete: true,
        onDelete: deleteRacketById,
      });
    } catch (e) {
      setAdminStatus(`DB 라켓 조회 에러: ${e}`, true);
    }
  }

  if (btnLoadAllRackets) {
    btnLoadAllRackets.addEventListener("click", handleLoadAllRackets);
  }

  // -----------------------------
  // 라켓 추가 버튼
  // -----------------------------

  async function handleAddRacket() {
    const name = adminNewName?.value.trim();
    const brand = adminNewBrand?.value.trim();

    if (!name || !brand) {
      setAdminStatus("라켓 이름과 브랜드는 필수입니다.", true);
      return;
    }

    const payload = {
      name,
      brand,
      power: adminNewPower?.value,
      control: adminNewControl?.value,
      spin: adminNewSpin?.value,
      weight: adminNewWeight?.value,
      tags: adminNewTags?.value,
    };

    try {
      setAdminStatus("라켓 추가 중...");
      const res = await fetch("/admin/rackets", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const text = await res.text();
        setAdminStatus(`라켓 추가 실패 (${res.status}) : ${text}`, true);
        return;
      }

      const data = await res.json();
      setAdminStatus(
        `라켓 추가 완료: ${data.racket?.name || "새 라켓"}`,
        false
      );

      adminNewName.value = "";
      adminNewBrand.value = "";
      if (adminNewPower) adminNewPower.value = "";
      if (adminNewControl) adminNewControl.value = "";
      if (adminNewSpin) adminNewSpin.value = "";
      if (adminNewWeight) adminNewWeight.value = "";
      if (adminNewTags) adminNewTags.value = "";

      await handleLoadAllRackets();
    } catch (e) {
      setAdminStatus(`라켓 추가 에러: ${e}`, true);
    }
  }

  if (btnAddRacket) {
    btnAddRacket.addEventListener("click", handleAddRacket);
  }

  // -----------------------------
  // 단건 삭제 함수
  // -----------------------------

  async function deleteRacketById(id) {
    if (!confirm(`ID ${id} 라켓을 삭제할까요?`)) {
      return;
    }

    try {
      setAdminStatus(`라켓 삭제 중... (ID: ${id})`);
      const res = await fetch(`/admin/rackets/${id}`, {
        method: "DELETE",
      });

      if (!res.ok) {
        const text = await res.text();
        setAdminStatus(`라켓 삭제 실패 (${res.status}) : ${text}`, true);
        return;
      }

      setAdminStatus(`라켓 삭제 완료 (ID: ${id})`);
      await handleLoadAllRackets();
    } catch (e) {
      setAdminStatus(`라켓 삭제 에러: ${e}`, true);
    }
  }

  // 첫 진입 시 관리 화면에 라켓 목록이 있다면 한 번 가져오기
  if (adminRacketListEl) {
    handleLoadAllRackets();
  }
});
