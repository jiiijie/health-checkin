// ===== 全局状态 =====
const CATEGORY_LABELS = {
    diet: "🍽️ 饮食",
    sleep: "😴 睡眠",
    exercise: " 运动",
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
        title: "️ 记录饮食",
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

    const config = QUICK_INPUT_CONFIG[currentQuickType];
    const fields = document.querySelectorAll("#modal-fields [data-field-name]");
    const values = {};
    fields.forEach((f) => {
        values[f.dataset.fieldName] = f.value.trim();
    });

    // 构建消息文本
    let message = "";
    if (currentQuickType === "water") {
        message = `我喝了${values.amount || "一杯水"}${values.note ? "，" + values.note : ""}`;
    } else if (currentQuickType === "diet") {
        message = `${values.meal || ""}吃了${values.content || "一些东西"}`;
    } else if (currentQuickType === "exercise") {
        message = `我${values.type ? "做了" + values.type : "运动了"}${values.duration ? values.duration + "分钟" : ""}`;
    } else if (currentQuickType === "sleep") {
        message = `昨晚${values.bedtime ? values.bedtime + "睡的" : ""}${values.wake_time ? "，" + values.wake_time + "起的" : ""}${values.quality ? "，睡眠质量" + values.quality : ""}`;
    }

    closeQuickInput();

    // 自动发送消息
    if (message) {
        document.getElementById("chat-input").value = message;
        await sendMessage();
    }
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
                `;
                historyList.appendChild(div);
            });
        }
    } catch (err) {
        console.error("加载统计失败", err);
    }
}

// 点击弹窗外部关闭
document.getElementById("quick-modal").addEventListener("click", function (e) {
    if (e.target === this) closeQuickInput();
});
