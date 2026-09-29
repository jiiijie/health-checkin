const chatMessages = document.getElementById("chat-messages");
const chatInput = document.getElementById("chat-input");
const btnSend = document.getElementById("btn-send");
const alertsArea = document.getElementById("alerts-area");
const summaryPanel = document.getElementById("summary-panel");
const summaryContent = document.getElementById("summary-content");
const historyPanel = document.getElementById("history-panel");
const historyContent = document.getElementById("history-content");

const CATEGORY_LABELS = {
    diet: "🍽️ 饮食",
    sleep: "😴 睡眠",
    exercise: "🏃 运动",
    water: "💧 饮水",
    other: "📝 其他",
};

async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    chatInput.value = "";
    btnSend.disabled = true;
    alertsArea.innerHTML = "";

    appendMessage("user", message);
    showTypingIndicator();

    try {
        const res = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message }),
        });
        const data = await res.json();

        removeTypingIndicator();
        appendMessage("assistant", data.reply);

        if (data.records && data.records.length > 0) {
            const recordText = data.records
                .map(
                    (r) =>
                        `${CATEGORY_LABELS[r.category] || r.category}：${r.content}`
                )
                .join("\n");
            appendMessage("assistant", `📝 已记录：\n${recordText}`);
        }

        if (data.alerts && data.alerts.length > 0) {
            data.alerts.forEach((alert) => {
                const div = document.createElement("div");
                div.className = "alert-item";
                div.textContent = alert;
                alertsArea.appendChild(div);
            });
        }
    } catch (err) {
        removeTypingIndicator();
        appendMessage("assistant", "哎呀，小眠走神了一下下…请再试一次吧 😣");
        console.error(err);
    }

    btnSend.disabled = false;
    chatInput.focus();
}

function appendMessage(role, text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${role}`;

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = role === "user" ? "😊" : "🌙";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.innerHTML = text.replace(/\n/g, "<br>");

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(bubble);
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    const div = document.createElement("div");
    div.className = "message assistant";
    div.id = "typing-indicator";
    div.innerHTML = `
        <div class="message-avatar">🌙</div>
        <div class="message-bubble">
            <div class="typing-indicator"><span></span><span></span><span></span></div>
        </div>
    `;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const el = document.getElementById("typing-indicator");
    if (el) el.remove();
}

async function loadSummary() {
    historyPanel.classList.add("hidden");
    summaryPanel.classList.toggle("hidden");

    if (summaryPanel.classList.contains("hidden")) return;

    summaryContent.innerHTML = '<div class="summary-item">加载中...</div>';

    try {
        const res = await fetch("/api/summary/today");
        const data = await res.json();

        let html = `
            <div class="summary-item">
                <strong>📊 总结</strong><br>${data.summary}
            </div>
            <div class="summary-item">
                <strong>💡 建议</strong><br>${data.suggestion}
            </div>
        `;

        if (data.records && data.records.length > 0) {
            html += '<div style="margin-top:12px;font-size:12px;color:#8b85a0;">今日记录：</div>';
            data.records.forEach((r) => {
                const label = CATEGORY_LABELS[r.category] || r.category;
                html += `
                    <div class="history-record">
                        <span class="record-time">${r.timestamp}</span>
                        <span class="record-content">
                            <span class="category-tag ${r.category}">${label}</span>
                            ${r.content}
                        </span>
                    </div>
                `;
            });
        }

        summaryContent.innerHTML = html;
    } catch (err) {
        summaryContent.innerHTML = '<div class="summary-item">获取总结失败，请稍后再试 😣</div>';
    }
}

async function loadHistory() {
    summaryPanel.classList.add("hidden");
    historyPanel.classList.toggle("hidden");

    if (historyPanel.classList.contains("hidden")) return;

    historyContent.innerHTML = '<div class="summary-item">加载中...</div>';

    try {
        const res = await fetch("/api/records");
        const records = await res.json();

        if (records.length === 0) {
            historyContent.innerHTML = '<div class="summary-item">还没有记录哦，快来打卡吧～</div>';
            return;
        }

        let html = "";
        const reversed = records.slice(-30).reverse();
        reversed.forEach((r) => {
            const label = CATEGORY_LABELS[r.category] || r.category;
            html += `
                <div class="history-record">
                    <span class="record-time">${r.date} ${r.timestamp}</span>
                    <span class="record-content">
                        <span class="category-tag ${r.category}">${label}</span>
                        ${r.content}
                    </span>
                </div>
            `;
        });

        historyContent.innerHTML = html;
    } catch (err) {
        historyContent.innerHTML = '<div class="summary-item">获取记录失败 😣</div>';
    }
}
