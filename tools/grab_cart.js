// 在原站上加两件商品并打开购物车，把面板整块 DOM 抓下来
const http = require("http");
const fs = require("fs");

function getJSON(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let d = "";
      res.on("data", (c) => (d += c));
      res.on("end", () => { try { resolve(JSON.parse(d)); } catch (e) { reject(e); } });
    }).on("error", reject);
  });
}
function connect(url) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(url);
    ws.onopen = () => resolve(ws);
    ws.onerror = reject;
  });
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const list = await getJSON("http://127.0.0.1:9222/json/list");
  const t = list.find((x) => x.type === "page");
  const ws = await connect(t.webSocketDebuggerUrl);
  let id = 0;
  const pend = new Map();
  ws.addEventListener("message", (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pend.has(m.id)) {
      const { res, rej } = pend.get(m.id);
      pend.delete(m.id);
      m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result);
    }
  });
  const call = (method, params) => new Promise((res, rej) => {
    const i = ++id; pend.set(i, { res, rej });
    ws.send(JSON.stringify({ id: i, method, params }));
  });

  await call("Page.enable", {});
  await call("Runtime.enable", {});
  await call("Emulation.setDeviceMetricsOverride", { width: 1410, height: 900, deviceScaleFactor: 1, mobile: false });
  await call("Page.navigate", { url: "http://wubu-pw.mysxl.cn/2" });
  await sleep(9000);

  const res = await call("Runtime.evaluate", {
    expression: `(async () => {
      const sleep = (ms) => new Promise(r => setTimeout(r, ms));
      const rows = document.querySelectorAll('.s-ecommerce-row-view-product');
      async function add(i, optIdx) {
        const row = rows[i]; if (!row) return;
        const sel = row.querySelector('select');
        if (sel) {
          const opts = Array.from(sel.options).filter(o => o.value && !o.disabled);
          const o = opts[optIdx] || opts[0];
          if (o) { sel.value = o.value; sel.dispatchEvent(new Event('change', { bubbles: true })); }
        }
        const btn = row.querySelector('.s-ecommerce-row-view-product-order-btn');
        if (btn) btn.click();
        await sleep(1200);
      }
      await add(0, 1);
      await add(1, 2);
      const num = (document.querySelector('.item-number') || {}).textContent;

      const cartIcon = document.querySelector('.s-shipping-cart-item');
      if (cartIcon) cartIcon.click();
      await sleep(3500);

      // 找同时包含「购物车」「小计」「下单结算」的元素，取最内层
      const cands = Array.from(document.querySelectorAll('div'))
        .filter(el => {
          const txt = el.textContent || '';
          const r = el.getBoundingClientRect();
          return /购物车/.test(txt) && /小计/.test(txt) && r.width > 500 && r.height > 300;
        })
        .sort((a, b) => a.getBoundingClientRect().width * a.getBoundingClientRect().height -
                        b.getBoundingClientRect().width * b.getBoundingClientRect().height);
      const panel = cands[0] || null;
      if (!panel) return { found: false, number: num };
      const r = panel.getBoundingClientRect();
      return {
        found: true,
        number: num,
        cls: (panel.className || '').toString(),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        html: panel.outerHTML
      };
    })()`,
    awaitPromise: true, returnByValue: true
  });

  const v = res.result.value;
  if (v && v.found) {
    fs.writeFileSync("raw/cart-panel.html", v.html, "utf8");
    fs.writeFileSync("raw/cart-panel.meta.json", JSON.stringify({
      number: v.number, cls: v.cls, rect: v.rect, bytes: v.html.length
    }, null, 1), "utf8");
    console.log(JSON.stringify({ number: v.number, cls: v.cls, rect: v.rect, bytes: v.html.length }, null, 1));
  } else {
    console.log("NOT FOUND", JSON.stringify(v));
  }
  ws.close();
})().catch((e) => { console.error("ERR", e); process.exit(1); });
