document.addEventListener("DOMContentLoaded", () => {
  const btnLoadAllRackets = document.getElementById("btnLoadAllRackets");
  const adminStatusEl = document.getElementById("adminStatus");
  const adminRacketListEl = document.getElementById("adminRacketList");

  // 기본 필드
  const adminNewName = document.getElementById("adminNewName");
  const adminNewBrand = document.getElementById("adminNewBrand");
  const adminNewPower = document.getElementById("adminNewPower");
  const adminNewControl = document.getElementById("adminNewControl");
  const adminNewSpin = document.getElementById("adminNewSpin");
  const adminNewWeight = document.getElementById("adminNewWeight");
  const adminNewTags = document.getElementById("adminNewTags");
  const adminNewUrl = document.getElementById("adminNewUrl");

  // 확장 스펙 필드
  const adminNewHeadSizeSqIn = document.getElementById("adminNewHeadSizeSqIn");
  const adminNewSwingweight = document.getElementById("adminNewSwingweight");
  const adminNewStiffnessRa = document.getElementById("adminNewStiffnessRa");
  const adminNewStringPattern = document.getElementById("adminNewStringPattern");
  const adminNewLengthMm = document.getElementById("adminNewLengthMm");
  const adminNewBalanceType = document.getElementById("adminNewBalanceType");
  const adminNewBeamWidthMm = document.getElementById("adminNewBeamWidthMm");
  const adminNewIsActive = document.getElementById("adminNewIsActive");

  const btnAddRacket = document.getElementById("btnAddRacket");

  function setAdminStatus(message, isError = false) {
    if (!adminStatusEl) return;
    adminStatusEl.textContent = message;
    adminStatusEl.classList.toggle("admin-status-error", !!isError);
  }

  function formatNumberOrDash(v) {
    if (v === null || v === undefined || Number.isNaN(v)) return "-";
    return String(v);
  }

  function normalizeBool(b) {
    if (typeof b === "boolean") return b;
    if (b === 1 || b === "1" || b === "true" || b === "TRUE") return true;
    if (b === 0 || b === "0" || b === "false" || b === "FALSE") return false;
    return false;
  }

  async function deleteRacket(id) {
    if (!confirm(`정말로 ID=${id} 라켓을 삭제하시겠습니까?`)) return;
    try {
      setAdminStatus(`라켓 삭제 중... (ID: ${id})`);
      const res = await fetch(`/admin/rackets/${id}`, {
        method: "DELETE",
      });
      if (!res.ok) {
        const text = await res.text();
        setAdminStatus(`라켓 삭제 실패: ${res.status} ${text}`, true);
        return;
      }
      setAdminStatus("라켓 삭제 완료");
      await handleLoadAllRackets();
    } catch (e) {
      setAdminStatus(`라켓 삭제 중 오류: ${e}`, true);
    }
  }

  async function updateRacket(id, payload) {
    try {
      setAdminStatus("라켓 정보 수정 중...");
      const res = await fetch(`/admin/rackets/${id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const text = await res.text();
        setAdminStatus(`라켓 수정 실패: ${res.status} ${text}`, true);
        return;
      }
      setAdminStatus("라켓 수정 완료");
      await handleLoadAllRackets();
    } catch (e) {
      setAdminStatus(`라켓 수정 중 오류: ${e}`, true);
    }
  }

  async function toggleRacketActive(id, nextActive) {
    const label = nextActive ? "활성화" : "비활성화";
    if (!confirm(`이 라켓을 ${label} 상태로 변경하시겠습니까?`)) return;
    await updateRacket(id, { isActive: nextActive });
  }

  function renderRacketList(list) {
    if (!adminRacketListEl) return;
    adminRacketListEl.innerHTML = "";

    if (!Array.isArray(list) || list.length === 0) {
      adminRacketListEl.textContent = "DB에 등록된 라켓이 없습니다.";
      return;
    }

    list.forEach((racket) => {
      const card = document.createElement("div");
      card.className = "racket-card";

      const header = document.createElement("div");
      header.className = "racket-header";

      const nameEl = document.createElement("div");
      nameEl.className = "racket-name";
      nameEl.textContent = racket.name || "(이름 없음)";
      header.appendChild(nameEl);

      // 점수/상태
      const scoreCol = document.createElement("div");
      scoreCol.className = "score-col";
      const power = racket.powerScore ?? racket.power;
      const control = racket.controlScore ?? racket.control;
      const spin = racket.spinScore ?? racket.spin;
      scoreCol.textContent = `P${formatNumberOrDash(
        power
      )} / C${formatNumberOrDash(control)} / S${formatNumberOrDash(spin)}`;
      header.appendChild(scoreCol);

      const buttonWrap = document.createElement("div");
      buttonWrap.style.display = "flex";
      buttonWrap.style.gap = "4px";

      const isActive =
        racket.isActive !== undefined
          ? normalizeBool(racket.isActive)
          : racket.is_active !== undefined
          ? normalizeBool(racket.is_active)
          : true;

      const activeBtn = document.createElement("button");
      activeBtn.className = "button button-secondary button-small";
      activeBtn.textContent = isActive ? "비활성으로" : "활성으로";
      activeBtn.addEventListener("click", () =>
        toggleRacketActive(racket.id, !isActive)
      );
      buttonWrap.appendChild(activeBtn);

      const delBtn = document.createElement("button");
      delBtn.className = "button button-secondary button-small";
      delBtn.textContent = "삭제";
      delBtn.addEventListener("click", () => deleteRacket(racket.id));
      buttonWrap.appendChild(delBtn);

      header.appendChild(buttonWrap);

      card.appendChild(header);

      // 브랜드 / 기본 무게
      const infoRow = document.createElement("div");
      infoRow.className = "racket-info-row";
      const weight =
        racket.unstrung_weight_g ??
        racket.unstrungWeight ??
        racket.weight ??
        "-";
      infoRow.textContent = `${racket.brand || "-"} · ${formatNumberOrDash(
        weight
      )} g`;
      card.appendChild(infoRow);

      // 스펙 줄
      const specRow = document.createElement("div");
      specRow.className = "racket-spec-row";

      const headSize =
        racket.head_size_sq_in ?? racket.headSize ?? racket.head_size;
      const lengthMm = racket.length_mm ?? racket.lengthMm;
      const swingweight = racket.swingweight;
      const stiffnessRa = racket.stiffness_ra ?? racket.stiffnessRa;
      const beamWidthMm = racket.beam_width_mm ?? racket.beamWidthMm;
      const pattern = racket.string_pattern ?? racket.stringPattern;

      const specParts = [];
      if (headSize) specParts.push(`${headSize} sq.in`);
      if (lengthMm) specParts.push(`${lengthMm} mm`);
      if (swingweight) specParts.push(`SW ${swingweight}`);
      if (stiffnessRa) specParts.push(`RA ${stiffnessRa}`);
      if (pattern) specParts.push(pattern);
      if (beamWidthMm) specParts.push(`Beam ${beamWidthMm} mm`);

      specRow.textContent =
        specParts.length > 0 ? specParts.join(" · ") : "스펙 정보 없음";
      card.appendChild(specRow);

      // 태그
      const tagsRow = document.createElement("div");
      tagsRow.className = "racket-tags";

      const tags =
        typeof racket.tags === "string"
          ? racket.tags.split(",").map((t) => t.trim()).filter(Boolean)
          : Array.isArray(racket.tags)
          ? racket.tags
          : [];

      tags.forEach((tag) => {
        const span = document.createElement("span");
        span.className = "racket-tag";
        span.textContent = tag;
        tagsRow.appendChild(span);
      });

      if (tags.length > 0) {
        card.appendChild(tagsRow);
      }

      // 상태 줄
      const statusRow = document.createElement("div");
      statusRow.className = "racket-info-row";
      statusRow.textContent = `상태: ${isActive ? "활성" : "비활성"}`;
      card.appendChild(statusRow);

      // 예약 URL 미리보기
      if (racket.url) {
        const urlRow = document.createElement("div");
        urlRow.className = "racket-info-row";
        urlRow.textContent = `예약 URL: ${racket.url}`;
        card.appendChild(urlRow);
      }

      adminRacketListEl.appendChild(card);
    });
  }

  async function handleLoadAllRackets() {
    try {
      setAdminStatus("DB 라켓 목록 조회 중...");
      const res = await fetch("/admin/rackets");
      if (!res.ok) {
        const text = await res.text();
        setAdminStatus(`조회 실패: ${res.status} ${text}`, true);
        return;
      }
      const data = await res.json();
      renderRacketList(data.rackets || []);
      setAdminStatus("라켓 목록 조회 완료");
    } catch (e) {
      setAdminStatus(`라켓 목록 조회 중 오류: ${e}`, true);
    }
  }

  async function handleAddRacket() {
    const name = adminNewName?.value?.trim();
    const brand = adminNewBrand?.value?.trim();

    if (!name || !brand) {
      setAdminStatus("라켓 이름과 브랜드는 필수입니다.", true);
      return;
    }

    const payload = {
      name,
      brand,
      power: adminNewPower?.value ? Number(adminNewPower.value) : null,
      control: adminNewControl?.value ? Number(adminNewControl.value) : null,
      spin: adminNewSpin?.value ? Number(adminNewSpin.value) : null,
      weight: adminNewWeight?.value ? Number(adminNewWeight.value) : null,
      tags: adminNewTags?.value || "",
      url: adminNewUrl?.value?.trim() || null,

      headSizeSqIn: adminNewHeadSizeSqIn?.value
        ? Number(adminNewHeadSizeSqIn.value)
        : null,
      swingweight: adminNewSwingweight?.value
        ? Number(adminNewSwingweight.value)
        : null,
      stiffnessRa: adminNewStiffnessRa?.value
        ? Number(adminNewStiffnessRa.value)
        : null,
      stringPattern: adminNewStringPattern?.value?.trim() || null,
      lengthMm: adminNewLengthMm?.value
        ? Number(adminNewLengthMm.value)
        : null,
      balanceType: adminNewBalanceType?.value?.trim() || null,
      beamWidthMm: adminNewBeamWidthMm?.value
        ? Number(adminNewBeamWidthMm.value)
        : null,
      isActive: adminNewIsActive ? adminNewIsActive.checked : true,
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
        setAdminStatus(`라켓 추가 실패: ${res.status} ${text}`, true);
        return;
      }

      // 폼 초기화
      if (adminNewName) adminNewName.value = "";
      if (adminNewBrand) adminNewBrand.value = "";
      if (adminNewPower) adminNewPower.value = "";
      if (adminNewControl) adminNewControl.value = "";
      if (adminNewSpin) adminNewSpin.value = "";
      if (adminNewWeight) adminNewWeight.value = "";
      if (adminNewTags) adminNewTags.value = "";
      if (adminNewUrl) adminNewUrl.value = "";
      if (adminNewHeadSizeSqIn) adminNewHeadSizeSqIn.value = "";
      if (adminNewSwingweight) adminNewSwingweight.value = "";
      if (adminNewStiffnessRa) adminNewStiffnessRa.value = "";
      if (adminNewStringPattern) adminNewStringPattern.value = "";
      if (adminNewLengthMm) adminNewLengthMm.value = "";
      if (adminNewBalanceType) adminNewBalanceType.value = "";
      if (adminNewBeamWidthMm) adminNewBeamWidthMm.value = "";
      if (adminNewIsActive) adminNewIsActive.checked = true;

      setAdminStatus("라켓 추가 완료");
      await handleLoadAllRackets();
    } catch (e) {
      setAdminStatus(`라켓 추가 에러: ${e}`, true);
    }
  }

  if (btnLoadAllRackets)
    btnLoadAllRackets.addEventListener("click", handleLoadAllRackets);
  if (btnAddRacket) btnAddRacket.addEventListener("click", handleAddRacket);

  // 첫 진입 시 자동 조회
  handleLoadAllRackets();
});
