// ===== 全局状态 =====
const CATEGORY_LABELS = {
    diet: "🍽️ 饮食",
    sleep: "😴 睡眠",
    exercise: "🏃 运动",
    water: "💧 饮水",
    other: "📝 其他",
};

// 快捷输入配置
const QUICK_INPUT_CONFIG = {
    water: {
        title: "💧 记录喝水",
        fields: [
            { name: "amount", label: "喝了多少？", type: "select", options: ["半杯 (100ml)", "一杯 (200ml)", "一瓶 (500ml)", "一大瓶 (1000ml)"] },
            { name: "note", label: "备注（可选）", type: "text", placeholder: "比如：温水、冰水..." },
        ],
    },
    diet: {
        title: "🍽️ 记录饮食",
        fields: [
            { name: "meal", label: "哪一餐？", type: "select", options: ["早餐", "午餐", "晚餐", "加餐/零食"] },
            { name: "content", label: "吃了什么？", type: "text", placeholder: "比如：一碗牛肉面、一个苹果..." },
        ],
    },
    exercise: {
        title: "🏃 记录运动",
        fields: [
            { name: "type", label: "运动类型", type: "text", placeholder: "比如：跑步、瑜伽、散步..." },
            { name: "duration", label: "运动时长（分钟）", type: "number", placeholder: "30" },
        ],
    },
    sleep: {
        title: "😴 记录睡眠",
        fields: [
            { name: "bedtime", label: "几点睡的？", type: "text", placeholder: "比如：23:30" },
            { name: "wake_time", label: "几点起的？", type: "text", placeholder: "比如：7:00" },
            { name: "quality", label: "睡眠质量", type: "select", options: ["很好", "一般", "不太好", "很差"] },
        ],
    },
};

let currentQuickType = null;

// ===== Tab 切换 =====
function switchTab(page) {
    document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));

    document.getElementById(`page-${page}`).classList.add("active");
    document.querySelector(`.tab-btn[data-page="${page}"]`).classList.add("active");

    if (page === "stats") loadStats();
    if (page === "profile") loadProfile();
}

// ===== 聊天功能 =====
async function sendMessage() {
    const input = document.getElementById("chat-input");
    const message = input.value.trim();
    if (!message) return;

    input.value = "";
    const btnSend = document.getElementById("btn-send");
    btnSend.disabled = true;
    document.getElementById("alerts-area").innerHTML = "";

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
                .map((r) => `${CATEGORY_LABELS[r.category] || r.category}：${r.content}`)
                .join("\n");
            appendMessage("assistant", `📝 已记录：\n${recordText}`);
        }

        if (data.alerts && data.alerts.length > 0) {
            data.alerts.forEach((alert) => {
                const div = document.createElement("div");
                div.className = "alert-item";
                div.textContent = alert;
                document.getElementById("alerts-area").appendChild(div);
            });
        }
    } catch (err) {
        removeTypingIndicator();
        appendMessage("assistant", "哎呀，小眠走神了一下下…请再试一次吧 😣");
        console.error(err);
    }

    btnSend.disabled = false;
    input.focus();
}

function appendMessage(role, text) {
    const chatMessages = document.getElementById("chat-messages");
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${role}`;

    const avatar = document.createElement("div");
    avatar.className = "msg-avatar";
    avatar.textContent = role === "user" ? "😊" : "🌙";

    const bubble = document.createElement("div");
    bubble.className = "msg-bubble";
    bubble.innerHTML = text.replace(/\n/g, "<br>");

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(bubble);
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    const chatMessages = document.getElementById("chat-messages");
    const div = document.createElement("div");
    div.className = "message assistant";
    div.id = "typing-indicator";
    div.innerHTML = `
        <div class="msg-avatar"></div>
        <div class="msg-bubble">
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

// ===== 快捷输入弹窗 =====
function showQuickInput(type) {
    currentQuickType = type;
    const config = QUICK_INPUT_CONFIG[type];
    if (!config) return;

    document.getElementById("modal-title").textContent = config.title;

    const fieldsContainer = document.getElementById("modal-fields");
    fieldsContainer.innerHTML = "";

    config.fields.forEach((field) => {
        const div = document.createElement("div");
        div.className = "modal-field";

        const label = document.createElement("label");
        label.textContent = field.label;
        div.appendChild(label);

        if (field.type === "select") {
            const select = document.createElement("select");
            select.name = field.name;
            select.dataset.fieldName = field.name;
            const defaultOpt = document.createElement("option");
            defaultOpt.value = "";
            defaultOpt.textContent = "请选择";
            select.appendChild(defaultOpt);
            field.options.forEach((opt) => {
                const option = document.createElement("option");
                option.value = opt;
                option.textContent = opt;
                select.appendChild(option);
            });
            div.appendChild(select);
        } else {
            const input = document.createElement("input");
            input.type = field.type || "text";
            input.name = field.name;
            input.dataset.fieldName = field.name;
            input.placeholder = field.placeholder || "";
            div.appendChild(input);
        }

        fieldsContainer.appendChild(div);
    });

    document.getElementById("quick-modal").classList.add("show");
}

function closeQuickInput() {
    document.getElementById("quick-modal").classList.remove("show");
    currentQuickType = null;
}

async function submitQuickRecord() {
    if (!currentQuickType) return;

    const fields = document.querySelectorAll("#modal-fields [data-field-name]");
    const values = {};
    fields.forEach((f) => {
        values[f.dataset.fieldName] = f.value.trim();
    });

    // 构建消息文本和结构化内容
    let message = "";
    let content = "";
    if (currentQuickType === "water") {
        message = `我喝了${values.amount || "一杯水"}${values.note ? "，" + values.note : ""}`;
        content = `饮水${values.amount || "一杯水"}`;
    } else if (currentQuickType === "diet") {
        message = `${values.meal || ""}吃了${values.content || "一些东西"}`;
        content = `${values.meal || ""}：${values.content || "一些东西"}`;
    } else if (currentQuickType === "exercise") {
        message = `我${values.type ? "做了" + values.type : "运动了"}${values.duration ? values.duration + "分钟" : ""}`;
        content = `${values.type || "运动"}${values.duration ? " " + values.duration + "分钟" : ""}`;
    } else if (currentQuickType === "sleep") {
        message = `昨晚${values.bedtime ? values.bedtime + "睡的" : ""}${values.wake_time ? "，" + values.wake_time + "起的" : ""}${values.quality ? "，睡眠质量" + values.quality : ""}`;
        content = `睡眠 ${values.bedtime || "?"}~${values.wake_time || "?"} 质量${values.quality || "一般"}`;
    }

    const category = currentQuickType;
    closeQuickInput();
    if (!message) return;

    // 显示用户消息
    const btnSend = document.getElementById("btn-send");
    btnSend.disabled = true;
    document.getElementById("alerts-area").innerHTML = "";
    appendMessage("user", message);
    showTypingIndicator();

    try {
        // 调用快捷记录 API（直接保存，不依赖 AI 解析）
        const res = await fetch("/api/quick-record", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ category: category, content, message }),
        });
        const data = await res.json();

        removeTypingIndicator();
        appendMessage("assistant", data.reply);

        if (data.records && data.records.length > 0) {
            const recordText = data.records
                .map((r) => `${CATEGORY_LABELS[r.category] || r.category}：${r.content}`)
                .join("\n");
            appendMessage("assistant", `📝 已记录：\n${recordText}`);
        }

        if (data.alerts && data.alerts.length > 0) {
            data.alerts.forEach((alert) => {
                const div = document.createElement("div");
                div.className = "alert-item";
                div.textContent = alert;
                document.getElementById("alerts-area").appendChild(div);
            });
        }
    } catch (err) {
        removeTypingIndicator();
        appendMessage("assistant", "哎呀，小眠走神了一下下…请再试一次吧 😣");
        console.error(err);
    }

    btnSend.disabled = false;
}

// ===== 档案功能 =====
async function loadProfile() {
    try {
        const res = await fetch("/api/profile");
        const data = await res.json();
        if (data && data.nickname) {
            document.getElementById("profile-display-name").textContent = data.nickname;
        }
        // 填充表单
        const fields = ["nickname", "gender", "age", "height", "weight", "waist", "arm", "leg", "chest", "target_weight", "daily_water", "daily_exercise", "target_sleep"];
        fields.forEach((f) => {
            const el = document.getElementById(`f-${f.replace("_", "-")}`) || document.querySelector(`[name="${f}"]`);
            if (el && data[f] !== undefined && data[f] !== null) {
                el.value = data[f];
            }
        });
    } catch (err) {
        console.error("加载档案失败", err);
    }
}

async function saveProfile(e) {
    e.preventDefault();
    const form = document.getElementById("profile-form");
    const formData = new FormData(form);
    const data = {};
    formData.forEach((value, key) => {
        if (value) {
            data[key] = key === "age" || key === "height" || key === "weight" || key === "waist" || key === "arm" || key === "leg" || key === "chest" || key === "target_weight" || key === "daily_water" || key === "daily_exercise" || key === "target_sleep"
                ? parseFloat(value)
                : value;
        }
    });

    try {
        const res = await fetch("/api/profile", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        const result = await res.json();
        if (result.success) {
            document.getElementById("profile-display-name").textContent = data.nickname || "我的档案";
            alert("档案保存成功！");
        }
    } catch (err) {
        alert("保存失败，请重试");
        console.error(err);
    }
}

// ===== 统计页 =====
async function loadStats() {
    const today = new Date().toLocaleDateString("zh-CN", { year: "numeric", month: "long", day: "numeric", weekday: "long" });
    document.getElementById("stats-date").textContent = today;

    try {
        const res = await fetch("/api/records");
        const records = await res.json();
        const todayStr = new Date().toISOString().split("T")[0];
        const todayRecords = records.filter((r) => r.date === todayStr);

        // 统计各项数量
        const counts = { water: 0, diet: 0, exercise: 0, sleep: 0 };
        todayRecords.forEach((r) => {
            if (counts[r.category] !== undefined) counts[r.category]++;
        });

        document.getElementById("stat-water").textContent = counts.water;
        document.getElementById("stat-diet").textContent = counts.diet;
        document.getElementById("stat-exercise").textContent = counts.exercise;
        document.getElementById("stat-sleep").textContent = counts.sleep;

        // 加载目标进度 + 提醒
        loadGoals();

        // 加载历史总结
        loadHistorySummaries();

        // 加载总结
        try {
            const summaryRes = await fetch("/api/summary/today");
            const summaryData = await summaryRes.json();
            document.getElementById("stats-summary-text").textContent = summaryData.summary || "今天还没有打卡记录哦～";
            document.getElementById("stats-suggestion-text").textContent = summaryData.suggestion || "记得记录今天的饮食和作息呀！";
        } catch (e) {
            // 忽略
        }

        // 加载历史记录
        const historyList = document.getElementById("stats-history-list");
        if (todayRecords.length === 0) {
            historyList.innerHTML = '<p class="empty-hint">今天还没有记录哦</p>';
        } else {
            historyList.innerHTML = "";
            const reversed = [...todayRecords].reverse();
            reversed.forEach((r) => {
                const label = CATEGORY_LABELS[r.category] || r.category;
                const div = document.createElement("div");
                div.className = "history-item";
                div.innerHTML = `
                    <span class="history-time">${r.timestamp}</span>
                    <span class="history-content">
                        <span class="category-tag ${r.category}">${label}</span>
                        ${r.content}
                    </span>
                    <span class="history-actions">
                        <button class="action-btn" title="编辑" onclick="showEditModal('${r.id}')">✏️</button>
                        <button class="action-btn" title="删除" onclick="deleteRecord('${r.id}')">🗑️</button>
                    </span>
                `;
                historyList.appendChild(div);
            });
        }
    } catch (err) {
        console.error("加载统计失败", err);
    }
}

// ===== 目标进度 =====
async function loadGoals() {
    try {
        const res = await fetch("/api/goals");
        const data = await res.json();

        const units = { water: "ml", exercise: "分钟", sleep: "小时" };
        ["water", "exercise", "sleep"].forEach((key) => {
            const g = data[key] || {};
            const fill = document.getElementById(`goal-${key}-fill`);
            const num = document.getElementById(`goal-${key}-num`);
            if (num) num.textContent = `${g.total || 0} / ${g.target || 0} ${units[key]}`;
            if (fill) {
                const pct = Math.min(g.percent || 0, 100);
                fill.style.width = pct + "%";
                fill.parentElement.title = `${pct}%`;
            }
        });

        const alertsBox = document.getElementById("goals-alerts");
        if (alertsBox) {
            if (data.alerts && data.alerts.length > 0) {
                alertsBox.innerHTML = data.alerts.map((a) => `<div class="goal-alert">${a}</div>`).join("");
            } else {
                alertsBox.innerHTML = '<div class="goal-alert ok">🎉 今日目标都达成啦，真棒！</div>';
            }
        }
    } catch (err) {
        console.error("加载目标失败", err);
    }
}

// ===== 历史总结 =====
async function loadHistorySummaries() {
    try {
        const res = await fetch("/api/summaries");
        const data = await res.json();
        const box = document.getElementById("history-summaries");
        if (!box) return;
        const list = (data && data.summaries) || [];
        if (list.length === 0) {
            box.innerHTML = '<p class="empty-hint">暂无历史总结（每晚 22:30 自动生成）</p>';
            return;
        }
        box.innerHTML = list
            .map((s) => {
                const tag = s.auto ? "自动" : "手动";
                return `<div class="history-summary-item">
                    <div class="hs-date">📅 ${s.date} <span class="hs-tag">${tag}</span></div>
                    <div class="hs-summary">${s.summary || ""}</div>
                    <div class="hs-suggestion">💡 ${s.suggestion || ""}</div>
                </div>`;
            })
            .join("");
    } catch (err) {
        console.error("加载历史总结失败", err);
    }
}

// 点击弹窗外部关闭
document.getElementById("quick-modal").addEventListener("click", function (e) {
    if (e.target === this) closeQuickInput();
});
document.getElementById("edit-modal").addEventListener("click", function (e) {
    if (e.target === this) closeEditModal();
});

// ===== 记录编辑 / 删除 =====
let editingRecordId = null;

async function showEditModal(recordId) {
    try {
        const res = await fetch(`/api/records/${recordId}`);
        const data = await res.json();
        if (!data.success || !data.record) {
            alert("记录不存在，可能已被删除");
            return;
        }
        editingRecordId = recordId;
        document.getElementById("edit-category").value = data.record.category;
        document.getElementById("edit-content").value = data.record.content;
        document.getElementById("edit-modal").classList.add("show");
    } catch (err) {
        console.error("打开编辑弹窗失败", err);
        alert("操作失败，请重试");
    }
}

function closeEditModal() {
    document.getElementById("edit-modal").classList.remove("show");
    editingRecordId = null;
}

async function saveRecordEdit() {
    if (!editingRecordId) return;

    const category = document.getElementById("edit-category").value;
    const content = document.getElementById("edit-content").value.trim();
    if (!content) {
        alert("内容不能为空");
        return;
    }

    try {
        const res = await fetch(`/api/records/${editingRecordId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ category, content }),
        });
        const data = await res.json();
        if (data.success) {
            closeEditModal();
            loadStats();
        } else {
            alert(data.message || "修改失败");
        }
    } catch (err) {
        console.error("修改失败", err);
        alert("修改失败，请重试");
    }
}

async function deleteRecord(recordId) {
    if (!confirm("确定删除这条记录吗？")) return;

    try {
        const res = await fetch(`/api/records/${recordId}`, { method: "DELETE" });
        const data = await res.json();
        if (data.success) {
            loadStats();
        } else {
            alert(data.message || "删除失败");
        }
    } catch (err) {
        console.error("删除失败", err);
        alert("删除失败，请重试");
    }
}
