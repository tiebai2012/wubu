// 把购物车面板用到的 CSS 规则整块抽出来
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

  // 先加购两件并打开面板，确保运行时的样式表已经注入
  await call("Runtime.evaluate", {
    expression: `(async () => {
      const sleep = (ms) => new Promise(r => setTimeout(r, ms));
      const rows = document.querySelectorAll('.s-ecommerce-row-view-product');
      async function add(i, o) {
        const row = rows[i]; if (!row) return;
        const sel = row.querySelector('select');
        if (sel) { const opts = Array.from(sel.options).filter(x => x.value && !x.disabled);
                   const t = opts[o] || opts[0]; if (t) { sel.value = t.value; sel.dispatchEvent(new Event('change', {bubbles:true})); } }
        const b = row.querySelector('.s-ecommerce-row-view-product-order-btn'); if (b) b.click();
        await sleep(1200);
      }
      await add(0, 0); await add(1, 0);
      const c = document.querySelector('.s-shipping-cart-item'); if (c) c.click();
      await sleep(3000);
      return true;
    })()`,
    awaitPromise: true, returnByValue: true
  });

  const res = await call("Runtime.evaluate", {
    expression: `(() => {
      const keys = ['buyer-checkout-dialog','cart-item-wrapper','shopping-container','cart-title',
                    'shopping-footer','s-kit-modal','quantity-panel','close-modal-icon','cart-panel'];
      const picked = [];
      const seen = new Set();
      for (const ss of document.styleSheets) {
        let rules = null;
        try { rules = ss.cssRules; } catch (e) { continue; }
        if (!rules) continue;
        for (const r of rules) {
          const txt = r.cssText || '';
          if (!txt) continue;
          if (keys.some(k => txt.includes(k))) {
            if (!seen.has(txt)) { seen.add(txt); picked.push(txt); }
          }
        }
      }
      return { count: picked.length, css: picked.join('\\n') };
    })()`,
    awaitPromise: true, returnByValue: true
  });

  const v = res.result.value;
  fs.writeFileSync("raw/cart-panel.css", v.css, "utf8");
  console.log("rules:", v.count, "bytes:", v.css.length);
  ws.close();
})().catch((e) => { console.error("ERR", e); process.exit(1); });
