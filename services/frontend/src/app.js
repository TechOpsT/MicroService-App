const API = "/api";
let token = localStorage.getItem("tf_token") || null;
let isRegister = false;

const authSection   = document.getElementById("auth-section");
const appSection    = document.getElementById("app-section");
const userInfo      = document.getElementById("user-info");
const authTitle     = document.getElementById("auth-title");
const authMsg       = document.getElementById("auth-msg");
const taskMsg       = document.getElementById("task-msg");
const registerExtra = document.getElementById("register-extra");
const taskList      = document.getElementById("task-list");

function showMsg(el, text, type = "error") {
  el.innerHTML = `<div class="msg msg-${type}">${text}</div>`;
  setTimeout(() => { el.innerHTML = ""; }, 4000);
}

async function apiFetch(path, opts = {}) {
  const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(API + path, { ...opts, headers });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}

function renderTasks(tasks) {
  if (!tasks.length) {
    taskList.innerHTML = '<li style="color:#9ca3af;font-size:.9rem">No tasks yet. Add one above!</li>';
    return;
  }
  taskList.innerHTML = tasks.map(t => `
    <li data-id="${t.id}">
      <div class="task-meta">
        <div class="task-title">${esc(t.title)}</div>
        ${t.description ? `<div class="task-desc">${esc(t.description)}</div>` : ""}
        <span class="badge badge-${t.status.replace(/ /g,"-")}">${t.status}</span>
      </div>
      <div class="task-actions">
        <select class="status-sel" data-id="${t.id}">
          <option value="pending"     ${t.status==="pending"?"selected":""}>Pending</option>
          <option value="in-progress" ${t.status==="in-progress"?"selected":""}>In Progress</option>
          <option value="done"        ${t.status==="done"?"selected":""}>Done</option>
        </select>
        <button class="btn btn-danger del-btn" data-id="${t.id}">Delete</button>
      </div>
    </li>
  `).join("");
}

function esc(str) {
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

async function loadTasks() {
  const { ok, data } = await apiFetch("/tasks");
  if (ok) renderTasks(data);
}

async function init() {
  if (token) {
    const { ok, data } = await apiFetch("/users/me");
    if (ok) {
      showApp(data.username);
      return;
    }
    localStorage.removeItem("tf_token");
    token = null;
  }
  authSection.style.display = "block";
}

function showApp(username) {
  authSection.style.display = "none";
  appSection.style.display = "block";
  userInfo.innerHTML = `<span>Hi, ${esc(username)}</span><button class="btn btn-danger" id="logout-btn">Logout</button>`;
  document.getElementById("logout-btn").addEventListener("click", () => {
    localStorage.removeItem("tf_token");
    token = null;
    userInfo.innerHTML = "";
    appSection.style.display = "none";
    authSection.style.display = "block";
  });
  loadTasks();
}

document.getElementById("auth-toggle-btn").addEventListener("click", () => {
  isRegister = !isRegister;
  authTitle.textContent = isRegister ? "Register" : "Login";
  document.getElementById("auth-submit-btn").textContent = isRegister ? "Register" : "Login";
  document.getElementById("auth-toggle-btn").textContent = isRegister ? "Switch to Login" : "Switch to Register";
  registerExtra.style.display = isRegister ? "flex" : "none";
  authMsg.innerHTML = "";
});

document.getElementById("auth-submit-btn").addEventListener("click", async () => {
  const email    = document.getElementById("auth-email").value.trim();
  const password = document.getElementById("auth-password").value;

  if (isRegister) {
    const username = document.getElementById("auth-username").value.trim();
    const { ok, data } = await apiFetch("/users/register", {
      method: "POST",
      body: JSON.stringify({ username, email, password }),
    });
    if (!ok) return showMsg(authMsg, data.error || "Registration failed");
    token = data.token;
    localStorage.setItem("tf_token", token);
    showApp(username);
  } else {
    const { ok, data } = await apiFetch("/users/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    if (!ok) return showMsg(authMsg, data.error || "Login failed");
    token = data.token;
    localStorage.setItem("tf_token", token);
    const meRes = await apiFetch("/users/me");
    showApp(meRes.ok ? meRes.data.username : "User");
  }
});

document.getElementById("add-task-btn").addEventListener("click", async () => {
  const title = document.getElementById("task-title").value.trim();
  const description = document.getElementById("task-desc").value.trim();
  if (!title) return showMsg(taskMsg, "Title is required");

  const { ok, data } = await apiFetch("/tasks", {
    method: "POST",
    body: JSON.stringify({ title, description }),
  });
  if (!ok) return showMsg(taskMsg, data.error || "Failed to create task");
  document.getElementById("task-title").value = "";
  document.getElementById("task-desc").value = "";
  showMsg(taskMsg, "Task added!", "success");
  loadTasks();
});

taskList.addEventListener("change", async (e) => {
  if (!e.target.classList.contains("status-sel")) return;
  const id = e.target.dataset.id;
  const { ok, data } = await apiFetch(`/tasks/${id}`, {
    method: "PUT",
    body: JSON.stringify({ status: e.target.value }),
  });
  if (!ok) showMsg(taskMsg, data.error || "Update failed");
  else loadTasks();
});

taskList.addEventListener("click", async (e) => {
  if (!e.target.classList.contains("del-btn")) return;
  const id = e.target.dataset.id;
  const { ok, data } = await apiFetch(`/tasks/${id}`, { method: "DELETE" });
  if (!ok) showMsg(taskMsg, data.error || "Delete failed");
  else loadTasks();
});

init();
