document.addEventListener("DOMContentLoaded", () => {
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

  function setAdminStatus(message, isError = false) {
    if (!adminStatusEl) return;
    adminStatusEl.textContent = message;
    adminStatusEl.classList.toggle("admin-status-error", !!isError);
  }

  function normalizeTags(rawTags) {
    if (!rawTags) return [];

    if (Array.isArray(rawTags)) {
      return rawTags
        .map((t) => String(t).trim())
        .filter((t) => t.length > 0);
    }

    if (typeof rawTags === "string") {
      return rawTags
        .split(/[,\s]+/)
        .map((t) => t.trim())
        .filter((t) => t.length > 0);
    }

    return [];
  }

  // 목록 렌더링
    // 라켓 목록 렌더링
  function renderRacketList(data) {
    const container = adminRacketListEl;
    if (!container) return;

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

      /* ---------- 헤더: ID + 이름 + 삭제 ---------- */
      const header = document.createElement("div");
      header.className = "racket-header";

      const name = document.createElement("div");
      name.className = "racket-name";
      const idLabel =
        typeof racket.id === "number" ? `${racket.id} ` : "";
      name.textContent = `${idLabel}${racket.name || "이름 없음"}`;
      header.appendChild(name);

      if (typeof racket.id === "number") {
        const delBtn = document.createElement("button");
        delBtn.className =
          "button button-secondary button-danger button-small";
        delBtn.textContent = "삭제";
        delBtn.addEventListener("click", () => deleteRacketById(racket.id));
        header.appendChild(delBtn);
      }

      card.appendChild(header);

      /* ---------- 브랜드 / 무게 줄 ---------- */
      const infoRow = document.createElement("div");
      infoRow.className = "racket-info-row";
      const brandText = racket.brand || "-";

      // weight 컬럼이 있으면 우선 사용, 없으면 unstrung_weight_g 사용
      const listedWeight =
        racket.weight ?? racket.unstrung_weight_g ?? null;
      const weightText = listedWeight ? `${listedWeight}g` : "-";

      infoRow.textContent = `브랜드: ${brandText} · 무게: ${weightText}`;
      card.appendChild(infoRow);

      /* ---------- 스펙 줄: 실제 있는 값만 모아서 표시 ---------- */
      const specRow = document.createElement("div");
      specRow.className = "racket-spec-row";

      const head = racket.head_size_sq_in ?? racket.head_size;
      const length = racket.length_mm;
      const balance = racket.balance_type;
      const sw = racket.swingweight;
      const ra = racket.stiffness_ra;
      const pattern = racket.string_pattern;
      const beam = racket.beam_width_mm;

      const specParts = [];

      if (head) specParts.push(`${head}sq`);
      if (length) specParts.push(`${length}mm`);
      if (listedWeight) specParts.push(`${listedWeight}g`);
      if (balance) specParts.push(balance);
      if (sw) specParts.push(`SW ${sw}`);
      if (ra) specParts.push(`RA ${ra}`);
      if (pattern) specParts.push(pattern);
      if (beam) specParts.push(`빔 ${beam}`);

      specRow.textContent =
        "스펙: " + (specParts.length > 0 ? specParts.join(" · ") : "정보 없음");
      card.appendChild(specRow);

      /* ---------- 점수 줄: P / C / S ---------- */
      const scoreParts = [];
      if (racket.power != null) scoreParts.push(`P${racket.power}`);
      if (racket.control != null) scoreParts.push(`C${racket.control}`);
      if (racket.spin != null) scoreParts.push(`S${racket.spin}`);

      if (scoreParts.length > 0) {
        const scoreRow = document.createElement("div");
        scoreRow.className = "racket-score-row";
        scoreRow.textContent = `점수: ${scoreParts.join(" · ")}`;
        card.appendChild(scoreRow);
      }

      /* ---------- 태그들 ---------- */
      const tagsBox = document.createElement("div");
      tagsBox.className = "racket-tags";

      if (racket.brand) {
        const tag = document.createElement("span");
        tag.className = "racket-tag";
        tag.textContent = racket.brand;
        tagsBox.appendChild(tag);
      }

      const tags = normalizeTags(racket.tags);
      tags.forEach((t) => {
        const tag = document.createElement("span");
        tag.className = "racket-tag";
        tag.textContent = t;
        tagsBox.appendChild(tag);
      });

      if (tagsBox.childElementCount > 0) {
        card.appendChild(tagsBox);
      }

      container.appendChild(card);
    });
  }


  // 삭제
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
      renderRacketList(data);
    } catch (e) {
      setAdminStatus(`DB 라켓 조회 에러: ${e}`, true);
    }
  }

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
      power: adminNewPower?.value ? Number(adminNewPower.value) : null,
      control: adminNewControl?.value ? Number(adminNewControl.value) : null,
      spin: adminNewSpin?.value ? Number(adminNewSpin.value) : null,
      weight: adminNewWeight?.value ? Number(adminNewWeight.value) : null,
      tags: adminNewTags?.value || "",
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

  if (btnLoadAllRackets)
    btnLoadAllRackets.addEventListener("click", handleLoadAllRackets);
  if (btnAddRacket) btnAddRacket.addEventListener("click", handleAddRacket);

  // 첫 진입 시 자동 조회
  handleLoadAllRackets();
});
