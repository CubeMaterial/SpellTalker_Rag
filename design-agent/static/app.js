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
  article.append(label, pre);
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
}

document.addEventListener("submit", async (event) => {
  const form = event.target;
  const button = form.querySelector("button[type='submit']");
  if (!button) return;

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
