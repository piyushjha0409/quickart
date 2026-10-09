const PRODUCTS = {
  bestsellers: [
    { id: "p1", name: "Amul Taaza Toned Milk", size: "500 ml", price: 28, mrp: 29, art: "🥛", tint: "#eaf1fb" },
    { id: "p2", name: "Farm fresh bananas (Robusta)", size: "6 pcs", price: 42, mrp: 55, art: "🍌", tint: "#fff5d6" },
    { id: "p3", name: "Onion", size: "1 kg", price: 39, mrp: 52, art: "🧅", tint: "#f8e9ef" },
    { id: "p4", name: "Tomato (Hybrid)", size: "500 g", price: 24, mrp: 30, art: "🍅", tint: "#fde8e4" },
    { id: "p5", name: "Brown eggs", size: "6 pcs", price: 69, mrp: 78, art: "🥚", tint: "#f6efe6" },
    { id: "p6", name: "Aashirvaad Whole Wheat Atta", size: "5 kg", price: 249, mrp: 295, art: "🌾", tint: "#f8f0dc" },
    { id: "p7", name: "Nandini Curd", size: "400 g", price: 32, mrp: 32, art: "🥣", tint: "#eef4f8" },
    { id: "p8", name: "Coriander leaves", size: "100 g", price: 9, mrp: 15, art: "🌿", tint: "#e3f4ea" },
  ],
  snacks: [
    { id: "s1", name: "Lay's India's Magic Masala", size: "52 g", price: 20, mrp: 20, art: "🥔", tint: "#e8f0fd" },
    { id: "s2", name: "Haldiram's Aloo Bhujia", size: "200 g", price: 55, mrp: 60, art: "🥨", tint: "#fff1dc" },
    { id: "s3", name: "Coca-Cola", size: "750 ml", price: 40, mrp: 45, art: "🥤", tint: "#fde6e6" },
    { id: "s4", name: "Maggi 2-Minute Masala Noodles", size: "4 × 70 g", price: 56, mrp: 60, art: "🍜", tint: "#fff5d1" },
    { id: "s5", name: "Dark Fantasy Choco Fills", size: "75 g", price: 40, mrp: 40, art: "🍪", tint: "#f1e9e3" },
    { id: "s6", name: "Tender coconut", size: "1 pc", price: 59, mrp: 70, art: "🥥", tint: "#e9f3e6" },
  ],
};

const inr = (n) => "₹" + Number(n).toLocaleString("en-IN", { maximumFractionDigits: 2 });

function minutesAgo(iso) {
  const mins = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.round(mins / 60);
  return `${hrs} hr${hrs > 1 ? "s" : ""} ago`;
}

/* ---------- Storefront ---------- */

const cart = new Map();
const allProducts = Object.values(PRODUCTS).flat();

function renderShelves() {
  for (const [shelf, items] of Object.entries(PRODUCTS)) {
    const grid = document.querySelector(`[data-shelf="${shelf}"]`);
    grid.innerHTML = items.map((p) => `
      <article class="product">
        <div class="product-art" style="--tint:${p.tint}" aria-hidden="true">${p.art}</div>
        <span class="product-time">9 mins</span>
        <h3 class="product-name">${p.name}</h3>
        <span class="product-size">${p.size}</span>
        <div class="product-foot">
          <span class="price">${inr(p.price)}${p.mrp > p.price ? `<s>${inr(p.mrp)}</s>` : ""}</span>
          <div data-qty="${p.id}"></div>
        </div>
      </article>`).join("");
  }
  allProducts.forEach((p) => renderQty(p.id));
}

function renderQty(id) {
  const slot = document.querySelector(`[data-qty="${id}"]`);
  const qty = cart.get(id) || 0;
  const name = allProducts.find((p) => p.id === id).name;
  slot.innerHTML = qty === 0
    ? `<button class="add" type="button" data-add="${id}" aria-label="Add ${name} to cart">ADD</button>`
    : `<div class="stepper">
         <button type="button" data-dec="${id}" aria-label="Remove one ${name}">−</button>
         <span aria-live="polite">${qty}</span>
         <button type="button" data-add="${id}" aria-label="Add one more ${name}">+</button>
       </div>`;
}

function renderCartButton() {
  let count = 0, total = 0;
  for (const [id, qty] of cart) {
    count += qty;
    total += qty * allProducts.find((p) => p.id === id).price;
  }
  document.getElementById("cart-label").textContent =
    count ? `${count} item${count > 1 ? "s" : ""} · ${inr(total)}` : "Cart";
}

document.addEventListener("click", (e) => {
  const add = e.target.closest("[data-add]");
  const dec = e.target.closest("[data-dec]");
  if (!add && !dec) return;
  const id = (add || dec).dataset[add ? "add" : "dec"];
  const next = (cart.get(id) || 0) + (add ? 1 : -1);
  next > 0 ? cart.set(id, next) : cart.delete(id);
  renderQty(id);
  renderCartButton();
  // Keep focus on the control the user is working with after re-render.
  const slot = document.querySelector(`[data-qty="${id}"]`);
  (slot.querySelector(add ? "[data-add]" : "[data-dec]") || slot.querySelector("button")).focus();
});

/* ---------- Customer context ---------- */

async function loadContext() {
  try {
    const res = await fetch("/api/context");
    if (!res.ok) return;
    const ctx = await res.json();
    document.getElementById("credits").textContent = inr(ctx.credits);

    const order = ctx.recent_orders?.[0];
    if (!order) return;
    const when = minutesAgo(order.placed_at);
    document.getElementById("last-order-title").textContent =
      order.status === "delivered" ? `Delivered ${when}` : `Order ${order.status}`;
    document.getElementById("last-order-meta").innerHTML =
      `Order <code>${order.id}</code> · ${inr(order.total)}`;
    document.getElementById("last-order").hidden = false;

    const strip = document.getElementById("chat-context");
    strip.innerHTML = `Your latest order: <code>${order.id}</code> · ${order.status} ${when} · ${inr(order.total)}`;
    strip.hidden = false;
  } catch {
    // Storefront still works without context; the chat strip just stays hidden.
  }
}

/* ---------- Chat widget ---------- */

async function loadModels() {
  try {
    const res = await fetch("/api/models");
    if (!res.ok) return;
    const { models, default: fallback } = await res.json();
    modelSelect.innerHTML = models.map((m) => {
      modelLabels[m.id] = m.label;
      const [input, , output] = m.price;
      return `<option value="${m.id}" title="$${input} in / $${output} out per 1M tokens" ${m.id === fallback ? "selected" : ""}>${m.label}</option>`;
    }).join("");
  } catch {
    // Without the list the server's default model answers.
  }
}

const launcher = document.getElementById("chat-launcher");
const panel = document.getElementById("chat-panel");
const log = document.getElementById("chat-log");
const welcome = document.getElementById("chat-welcome");
const form = document.getElementById("chat-form");
const input = document.getElementById("chat-text");
const sendBtn = document.getElementById("chat-send");
const modelSelect = document.getElementById("chat-model");
const effortSelect = document.getElementById("chat-effort");
const modelLabels = {};

// One conversation per page load; the server keeps its history under this id.
let threadId = null;
let busy = false;

function openChat(prefill) {
  panel.hidden = false;
  launcher.setAttribute("aria-expanded", "true");
  if (prefill) input.value = prefill;
  autosize();
  input.focus();
}

function closeChat() {
  panel.hidden = true;
  launcher.setAttribute("aria-expanded", "false");
  launcher.focus();
}

launcher.addEventListener("click", () => openChat());
document.getElementById("chat-close").addEventListener("click", closeChat);
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !panel.hidden) closeChat();
});
document.querySelectorAll("[data-open-chat]").forEach((btn) =>
  btn.addEventListener("click", () => openChat(btn.dataset.prefill)));

document.getElementById("chat-reset").addEventListener("click", () => {
  threadId = null;
  log.querySelectorAll(".msg, .msg-meta, .typing").forEach((el) => el.remove());
  welcome.hidden = false;
  input.value = "";
  input.focus();
});

log.addEventListener("click", (e) => {
  const chip = e.target.closest("[data-suggest]");
  if (chip) send(chip.textContent);
});

form.addEventListener("submit", (e) => {
  e.preventDefault();
  send(input.value);
});

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    form.requestSubmit();
  }
});
input.addEventListener("input", autosize);

function autosize() {
  input.style.height = "auto";
  input.style.height = input.scrollHeight + "px";
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// Just enough Markdown for agent replies: paragraphs, lists, **bold**, `code`.
function renderMarkdown(text) {
  const inline = (s) => escapeHtml(s)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
  const LIST = { ul: /^\s*[-*•]\s+/, ol: /^\s*\d+[.)]\s+/ };

  const out = [];
  let para = [], list = null;
  const flushPara = () => { if (para.length) out.push(`<p>${para.map(inline).join("<br>")}</p>`); para = []; };
  const flushList = () => { if (list) out.push(`<${list.tag}>${list.items.join("")}</${list.tag}>`); list = null; };

  for (const line of text.trim().split("\n")) {
    const tag = LIST.ul.test(line) ? "ul" : LIST.ol.test(line) ? "ol" : null;
    if (tag) {
      flushPara();
      if (list?.tag !== tag) { flushList(); list = { tag, items: [] }; }
      list.items.push(`<li>${inline(line.replace(LIST[tag], ""))}</li>`);
    } else if (!line.trim()) {
      flushPara(); flushList();
    } else {
      flushList();
      para.push(line);
    }
  }
  flushPara(); flushList();
  return out.join("");
}

function addMessage(role, html) {
  welcome.hidden = true;
  const el = document.createElement("div");
  el.className = `msg msg-${role}`;
  el.innerHTML = html;
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
  return el;
}

function setBusy(value) {
  busy = value;
  sendBtn.disabled = value;
}

async function send(raw) {
  const text = raw.trim();
  if (!text || busy) return;

  addMessage("user", `<p>${escapeHtml(text).replace(/\n/g, "<br>")}</p>`);
  input.value = "";
  autosize();
  setBusy(true);

  const typing = document.createElement("div");
  typing.className = "msg msg-agent typing";
  typing.setAttribute("aria-label", "Support is typing");
  typing.innerHTML = "<span></span><span></span><span></span>";
  log.appendChild(typing);
  log.scrollTop = log.scrollHeight;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        thread_id: threadId,
        model: modelSelect.value || undefined,
        effort: effortSelect.value,
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    threadId = data.thread_id;
    typing.remove();
    addMessage("agent", renderMarkdown(data.reply));
    const meta = document.createElement("p");
    meta.className = "msg-meta";
    const effort = data.effort_reason ? `${data.effort} (auto: ${data.effort_reason})` : data.effort;
    meta.textContent = `${modelLabels[data.model] || data.model} · ${effort} · ${data.seconds.toFixed(1)} s · $${data.cost_usd.toFixed(4)}`;
    log.appendChild(meta);
    log.scrollTop = log.scrollHeight;
  } catch {
    typing.remove();
    const err = addMessage("error", "<p>Message not delivered. Check that the server is running, then retry.</p><button type=\"button\">Retry</button>");
    err.querySelector("button").addEventListener("click", () => {
      err.previousElementSibling?.remove(); // drop the user bubble; send() re-adds it
      err.remove();
      send(text);
    });
  } finally {
    setBusy(false);
    input.focus();
  }
}

renderShelves();
loadContext();
loadModels();
