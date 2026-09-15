function appendMessage(role, content) {
  const messages = document.querySelector("#messages");
  if (!messages) return;
  const empty = messages.querySelector(".muted");
  if (empty) empty.remove();
  const article = document.createElement("article");
  article.className = `message ${role}`;
  const label = document.createElement("div");
  label.className = "message-role";
  label.textContent = role === "user" ? "User" : "Agent";
  const pre = document.createElement("pre");
  pre.textContent = content;
  const copyButton = createCopyButton();
  article.append(label, copyButton, pre);
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
}

function createCopyButton() {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "copy-message";
  button.textContent = "복사";
  return button;
}

async function copyMessage(button) {
  const message = button.closest(".message");
  const pre = message?.querySelector("pre");
  if (!pre) return;
  const text = pre.textContent || "";
  try {
    await navigator.clipboard.writeText(text);
    button.textContent = "복사됨";
  } catch (_error) {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(pre);
    selection.removeAllRanges();
    selection.addRange(range);
    button.textContent = "선택됨";
  }
  window.setTimeout(() => {
    button.textContent = "복사";
  }, 1200);
}

function collectDataTablePayload(form) {
  const table = form.querySelector(".data-table");
  if (!table) return null;
  const headers = JSON.parse(table.dataset.headers || "[]");
  const rows = Array.from(table.querySelectorAll("tbody tr")).map((tr) => {
    const row = {};
    headers.forEach((header) => {
      const input = tr.querySelector(`input[data-field="${CSS.escape(header)}"]`);
      row[header] = input ? input.value : "";
    });
    return row;
  });
  return {headers, rows};
}

function createDataRow(table) {
  const headers = JSON.parse(table.dataset.headers || "[]");
  const tr = document.createElement("tr");
  const tools = document.createElement("td");
  tools.className = "row-tools";
  const deleteButton = document.createElement("button");
  deleteButton.type = "button";
  deleteButton.className = "delete-row";
  deleteButton.textContent = "Delete";
  tools.append(deleteButton);
  tr.append(tools);
  headers.forEach((header) => {
    const td = document.createElement("td");
    const input = document.createElement("input");
    input.type = "text";
    input.dataset.field = header;
    td.append(input);
    tr.append(td);
  });
  return tr;
}

document.addEventListener("click", (event) => {
  const copyButton = event.target.closest(".copy-message");
  if (copyButton) {
    copyMessage(copyButton);
    return;
  }

  const deleteButton = event.target.closest(".delete-row");
  if (deleteButton) {
    deleteButton.closest("tr")?.remove();
    return;
  }

  if (event.target.id === "add-data-row") {
    const table = document.querySelector(".data-table");
    const tbody = table?.querySelector("tbody");
    if (table && tbody) tbody.append(createDataRow(table));
  }
});

document.addEventListener("submit", async (event) => {
  const form = event.target;
  const button = form.querySelector("button[type='submit']");
  if (!button) return;

  if (form.id === "data-table-form") {
    const payload = collectDataTablePayload(form);
    if (payload) {
      form.querySelector("#data-payload").value = JSON.stringify(payload);
    }
  }

  if (form.id === "chat-form") {
    event.preventDefault();
    const textarea = form.querySelector("textarea[name='message']");
    const message = textarea.value.trim();
    if (!message) return;
    const payload = {
      session_id: form.querySelector("input[name='session_id']").value,
      message,
      write_mode: form.querySelector("input[name='write_mode']").checked,
    };
    appendMessage("user", message);
    textarea.value = "";
    button.textContent = "처리 중...";
    button.disabled = true;
    try {
      const response = await fetch("/chat/message", {
        method: "POST",
        headers: {"Content-Type": "application/json; charset=UTF-8"},
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "요청 실패");
      if (data.session_id) {
        form.querySelector("input[name='session_id']").value = data.session_id;
        const chatLayout = document.querySelector(".chat-layout");
        if (chatLayout) chatLayout.dataset.sessionId = data.session_id;
        if (window.location.pathname === "/chat") {
          window.history.replaceState(null, "", `/chat/${data.session_id}`);
        }
      }
      appendMessage("assistant", data.reply);
      if (data.has_pending_change) {
        window.location.href = `/chat/${data.session_id}`;
      }
    } catch (error) {
      appendMessage("assistant", `오류: ${error.message}`);
    } finally {
      button.textContent = "전송";
      button.disabled = false;
    }
    return;
  }

  button.dataset.originalText = button.textContent;
  button.textContent = "처리 중...";
  button.disabled = true;
});
