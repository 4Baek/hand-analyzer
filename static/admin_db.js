// admin_db.js

document.addEventListener("DOMContentLoaded", () => {
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

  function setAdminStatus(message, isError = false) {
    if (!adminStatusEl) return;
    adminStatusEl.textContent = message;
    adminStatusEl.classList.toggle("admin-status-error", !!isError);
  }

  // 라켓 목록 렌더링 + 단건 삭제 버튼
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

      const header = document.createElement("div");
      header.className = "racket-header";

      const name = document.createElement("div");
      name.className = "racket-name";
      name.textContent = racket.name || "이름 없음";

      const spec = document.createElement("div");
      spec.className = "racket-score";

      // P / C / S 를 각각 한 칸씩 만들기
      [
      { label: "P", value: racket.power },
      { label: "C", value: racket.control },
      { label: "S", value: racket.spin },
      ].forEach(({ label, value }) => {
      const span = document.createElement("span");
      span.className = "score-item";
      span.textContent = `${label}${value ?? "-"}`;
      spec.appendChild(span);
      });

      header.appendChild(name);
      header.appendChild(spec);

      // ---- 단건 삭제 버튼 추가 ----
      if (typeof racket.id === "number") {
        const delBtn = document.createElement("button");
        delBtn.className =
          "button button-secondary button-danger button-small";
        delBtn.textContent = "삭제";
        delBtn.addEventListener("click", () => deleteRacketById(racket.id));
        header.appendChild(delBtn);
      }

      card.appendChild(header);

      const tagsBox = document.createElement("div");
      tagsBox.className = "racket-tags";

      const brand = racket.brand;
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

  // ---- 단건 삭제 함수 ----
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

  if (btnResetDb) btnResetDb.addEventListener("click", handleResetDb);
  if (btnLoadAllRackets)
    btnLoadAllRackets.addEventListener("click", handleLoadAllRackets);
  if (btnAddRacket) btnAddRacket.addEventListener("click", handleAddRacket);

  // 첫 진입 시 목록 한 번 가져오기
  handleLoadAllRackets();
});
