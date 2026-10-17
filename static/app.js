const $ = (id) => document.getElementById(id);
const KEY = "prep-attempt";
const TOKEN_KEY = "prep-token";
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
// The server sends microseconds; trim to milliseconds so every browser parses it.
const ms = (s) => Date.parse(s.replace(/(\.\d{3})\d+/, "$1"));

let S = null;       // current attempt: id, deadline, offset, questions, answers, flags, i
let tick = null;
let busy = false;
let R = null;       // results from the server, kept for the review screen
let tab = "missed"; // which review tab is open

function show(name) {
  document.querySelectorAll(".view").forEach((v) => (v.hidden = v.id !== name));
}

// ---------- token ----------
function getToken() {
  try { return localStorage.getItem(TOKEN_KEY); } catch (e) { return null; }
}
function setToken(t) {
  try { localStorage.setItem(TOKEN_KEY, t); } catch (e) {}
}
function clearToken() {
  try { localStorage.removeItem(TOKEN_KEY); } catch (e) {}
}
const jsonPost = (obj) => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(obj),
});

// Sends the token with every request. Errors carry status, detail and code.
async function api(path, opts) {
  opts = opts || {};
  const headers = { ...(opts.headers || {}) };
  const token = getToken();
  if (token) headers.Authorization = "Bearer " + token;
  const r = await fetch(path, { ...opts, headers });
  let body = null;
  try { body = await r.json(); } catch (e) {}
  if (!r.ok) {
    const err = new Error("request failed");
    err.status = r.status;
    err.detail = body && body.detail;
    err.code = err.detail && err.detail.code;
    throw err;
  }
  return body;
}

function save() {
  try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {}
}
function clearSaved() {
  try { localStorage.removeItem(KEY); } catch (e) {}
}

// ---------- auth ----------
function authMessage(e) {
  if (e.status === 401) return "Incorrect email or password.";
  if (e.status === 400 && typeof e.detail === "string") return e.detail;
  if (e.status === 422) return "Check your details: a username, a valid email, and a password of at least 4 characters.";
  return "Could not reach the server. Please try again.";
}

async function authenticate(isRegister) {
  const username = $("username").value.trim();
  const email = $("email").value.trim();
  const password = $("password").value;
  $("authMsg").textContent = "";
  $("loginBtn").disabled = true;
  $("registerBtn").disabled = true;
  try {
    if (isRegister) await api("/auth/register", jsonPost({ username, email, password }));
    const t = await api("/auth/login", jsonPost({ email, password }));
    setToken(t.access_token);
    $("password").value = "";
    if (S) begin(); // a test was in progress before the login screen appeared
    else show("start");
  } catch (e) {
    $("authMsg").textContent = authMessage(e);
  }
  $("loginBtn").disabled = false;
  $("registerBtn").disabled = false;
}

function logout() {
  clearToken();
  clearSaved();
  clearInterval(tick);
  S = null;
  $("authMsg").textContent = "";
  show("auth");
}

// ---------- start ----------
async function startTest() {
  $("startBtn").disabled = true;
  $("startMsg").textContent = "";
  try {
    const d = await api("/tests", { method: "POST" });
    S = {
      id: d.attempt_id,
      deadline: ms(d.deadline),
      offset: ms(d.server_time) - Date.now(), // server clock minus this device's clock
      questions: d.questions,
      answers: {},
      flags: {},
      i: 0,
    };
    save();
    begin();
  } catch (e) {
    if (e.status === 401) {
      clearToken();
      show("auth");
      $("authMsg").textContent = "Please log in to start.";
    } else if (e.status === 402) {
      $("startMsg").textContent = "You have used all your free tests.";
    } else {
      $("startMsg").textContent = "Could not start the test. Please try again.";
    }
  }
  $("startBtn").disabled = false;
}

function begin() {
  show("test");
  $("testMsg").textContent = "";
  render();
  clearInterval(tick);
  tick = setInterval(updateTimer, 1000);
  updateTimer();
}

// ---------- timer ----------
// Recomputed from the server's deadline every second, so a sleeping tab can't drift.
function updateTimer() {
  const left = Math.max(0, Math.round((S.deadline - (Date.now() + S.offset)) / 1000));
  const t = $("timer");
  t.textContent = String(Math.floor(left / 60)).padStart(2, "0") + ":" + String(left % 60).padStart(2, "0");
  t.className = left <= 60 ? "danger" : left <= 600 ? "warn" : "";
  if (left === 0) {
    clearInterval(tick);
    submit(true);
  }
}

// ---------- question view ----------
function render() {
  const q = S.questions[S.i];
  $("section").textContent = cap(q.section);
  $("progress").textContent = "Question " + (S.i + 1) + " of " + S.questions.length;
  $("passage").hidden = !q.passage;
  $("passage").textContent = q.passage || "";
  $("qtext").textContent = q.question;

  const box = $("options");
  box.textContent = "";
  "abcde".split("").forEach((k) => {
    const b = document.createElement("button");
    b.className = "opt" + (S.answers[q.id] === k ? " sel" : "");
    b.textContent = k.toUpperCase() + ".  " + q.options[k]; // textContent, never innerHTML
    b.onclick = () => choose(k);
    box.appendChild(b);
  });

  $("flag").textContent = S.flags[q.id] ? "Remove flag" : "Flag for review";
  $("prev").disabled = S.i === 0;
  $("next").disabled = S.i === S.questions.length - 1;
  renderNav();
}

function renderNav() {
  const nav = $("nav");
  nav.textContent = "";
  let last = "";
  S.questions.forEach((q, n) => {
    if (q.section !== last) {
      last = q.section;
      const h = document.createElement("div");
      h.className = "navhead";
      h.textContent = q.section;
      nav.appendChild(h);
    }
    const b = document.createElement("button");
    b.textContent = n + 1;
    b.className = "n" + (S.answers[q.id] ? " done" : "") + (S.flags[q.id] ? " flag" : "") + (n === S.i ? " cur" : "");
    b.onclick = () => go(n);
    nav.appendChild(b);
  });
}

function go(n) {
  S.i = n;
  save();
  render();
  window.scrollTo(0, 0);
}

function choose(k) {
  const id = S.questions[S.i].id;
  if (S.answers[id] === k) delete S.answers[id]; // tap again to deselect
  else S.answers[id] = k;
  save();
  render();
}

function toggleFlag() {
  const id = S.questions[S.i].id;
  if (S.flags[id]) delete S.flags[id];
  else S.flags[id] = true;
  save();
  render();
}

// ---------- submit ----------
async function submit(auto) {
  if (busy) return;
  if (!auto) {
    const un = S.questions.filter((q) => !S.answers[q.id]).length;
    const fl = S.questions.filter((q) => S.flags[q.id]).length;
    if (!confirm(un + " unanswered, " + fl + " flagged. Submit now?")) return;
  }
  busy = true;
  clearInterval(tick);
  $("testMsg").textContent = "Submitting...";
  try {
    try {
      await api("/tests/" + S.id + "/submit", jsonPost({ answers: S.answers }));
    } catch (e) {
      if (e.code !== "already_submitted") throw e; // already in: just fetch the results
    }
    const r = await api("/tests/" + S.id + "/results");
    clearSaved();
    showResults(r);
  } catch (e) {
    handleError(e);
  }
  busy = false;
}

function handleError(e) {
  if (e.status === 401) {
    // Logged out or token expired. The test stays saved, so logging in resumes it.
    clearToken();
    show("auth");
    $("authMsg").textContent = "Your login expired. Log in again to continue.";
    return;
  }
  if (e.code === "deadline_passed") {
    fail("Time ran out before your answers reached the server, so this attempt could not be submitted.");
  } else if (e.code === "attempt_not_found") {
    fail("This test could not be found on the server. Please start a new test.");
  } else {
    // network trouble: keep everything, let the person retry
    $("testMsg").textContent = "Could not reach the server. Your answers are kept. Press Submit to try again.";
  }
}

function fail(msg) {
  clearSaved();
  S = null;
  show("start");
  $("startMsg").textContent = msg;
}

// ---------- results (minimal for now) ----------
function showResults(r) {
  R = r;
  show("results");
  $("overall").textContent = r.overall.correct + " / " + r.overall.total + " (" + r.overall.percent.toFixed(1) + "%)";
  const t = r.time_taken_seconds;
  $("taken").textContent = "Time taken: " + Math.floor(t / 60) + " min " + (t % 60) + " s";
  const box = $("secs");
  box.textContent = "";
  Object.entries(r.sections).forEach(([name, s]) => {
    const d = document.createElement("div");
    d.className = "card";
    d.textContent = cap(name) + ": " + s.correct + " / " + s.total + " (" + s.percent.toFixed(1) + "%)";
    box.appendChild(d);
  });
}

// ---------- review ----------
function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

function showReview() {
  const missed = R.review.filter((x) => !x.is_correct).length;
  tab = missed > 0 ? "missed" : "all";
  show("review");
  renderReview();
  window.scrollTo(0, 0);
}

function renderReview() {
  const items = R.review.map((x, n) => ({ ...x, n: n + 1 }));
  const shown = tab === "missed" ? items.filter((x) => !x.is_correct) : items;
  $("tabMissed").classList.toggle("on", tab === "missed");
  $("tabAll").classList.toggle("on", tab === "all");
  $("reviewCount").textContent = shown.length + (shown.length === 1 ? " question" : " questions");
  const list = $("reviewList");
  list.textContent = "";
  if (shown.length === 0) {
    list.appendChild(el("p", null, "Nothing missed. Nice work."));
    return;
  }
  shown.forEach((x) => list.appendChild(reviewCard(x)));
}

function reviewCard(x) {
  const card = el("article", "rcard");
  const status = x.your_answer === null ? "skipped" : x.is_correct ? "correct" : "wrong";

  const head = el("div", "rhead");
  head.appendChild(el("span", null, "Q" + x.n + " · " + cap(x.section)));
  head.appendChild(el("span", "badge " + status, cap(status)));
  card.appendChild(head);

  if (x.passage) {
    const d = el("details", "rpassage");
    d.appendChild(el("summary", null, "Show passage"));
    d.appendChild(el("div", null, x.passage));
    card.appendChild(d);
  }
  card.appendChild(el("p", "qtext", x.question));

  const opts = el("div", "ropts");
  "abcde".split("").forEach((k) => {
    if (!x.options[k]) return;
    const isRight = k === x.correct_answer;
    const isMine = k === x.your_answer;
    const row = el("div", "ropt" + (isRight ? " right" : isMine ? " mine" : ""), k.toUpperCase() + ".  " + x.options[k]);
    if (isRight && isMine) row.appendChild(el("span", "tag", "Your answer · correct"));
    else if (isRight) row.appendChild(el("span", "tag", "Correct answer"));
    else if (isMine) row.appendChild(el("span", "tag", "Your answer"));
    opts.appendChild(row);
  });
  card.appendChild(opts);

  if (x.explanation) {
    const ex = el("div", "rexp");
    ex.appendChild(el("strong", null, "Explanation"));
    ex.appendChild(el("p", null, x.explanation));
    card.appendChild(ex);
  }
  return card;
}

// ---------- wiring ----------
$("startBtn").onclick = startTest;
$("loginBtn").onclick = () => authenticate(false);
$("registerBtn").onclick = () => authenticate(true);
$("logoutBtn").onclick = logout;
$("prev").onclick = () => go(S.i - 1);
$("next").onclick = () => go(S.i + 1);
$("flag").onclick = toggleFlag;
$("submitBtn").onclick = () => submit(false);
$("again").onclick = () => { S = null; show("start"); };
$("reviewBtn").onclick = showReview;
$("backBtn").onclick = () => show("results");
$("tabMissed").onclick = () => { tab = "missed"; renderReview(); };
$("tabAll").onclick = () => { tab = "all"; renderReview(); };
document.addEventListener("keydown", (e) => {
  if (!S || $("test").hidden || e.ctrlKey || e.metaKey || e.altKey) return;
  if (e.key === "ArrowRight" && S.i < S.questions.length - 1) go(S.i + 1);
  else if (e.key === "ArrowLeft" && S.i > 0) go(S.i - 1);
  else if (e.key.length === 1 && "abcde".includes(e.key.toLowerCase())) choose(e.key.toLowerCase());
});

// ---------- startup ----------
// Restore an unfinished test after a refresh, but only for someone who is logged in.
try {
  const saved = localStorage.getItem(KEY);
  if (saved) S = JSON.parse(saved);
} catch (e) {
  clearSaved();
  S = null;
}
if (!getToken()) show("auth");
else if (S) begin();
else show("start");
