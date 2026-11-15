// 在购物车里点「下单结算」，看原站到底发生什么
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
      const row = document.querySelector('.s-ecommerce-row-view-product');
      const sel = row && row.querySelector('select');
      if (sel) { const o = Array.from(sel.options).find(x => x.value && !x.disabled);
                 if (o) { sel.value = o.value; sel.dispatchEvent(new Event('change',{bubbles:true})); } }
      const add = row && row.querySelector('.s-ecommerce-row-view-product-order-btn');
      if (add) add.click();
      await sleep(1500);
      const cart = document.querySelector('.s-shipping-cart-item');
      if (cart) cart.click();
      await sleep(2500);

      const before = location.href;
      const btn = document.querySelector('.checkout-btn');
      const btnInfo = btn ? { text: btn.textContent.trim(), tag: btn.tagName, cls: btn.className } : null;
      if (btn) btn.click();
      await sleep(4000);

      const after = location.href;
      const dialogs = Array.from(document.querySelectorAll('.s-kit-modal, .s-kit-modal-wrap, [role=dialog]'))
        .filter(el => { const r = el.getBoundingClientRect(); return r.width > 100 && r.height > 80; })
        .map(el => ({
          cls: (el.className || '').toString().slice(0, 90),
          text: (el.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 300)
        }));
      return { before, after, btnInfo, dialogs: dialogs.slice(0, 4) };
    })()`,
    awaitPromise: true, returnByValue: true
  });
  console.log(JSON.stringify(res.result.value, null, 1));
  const shot = await call("Page.captureScreenshot", { format: "png" });
  fs.writeFileSync("raw/checkout-click.png", Buffer.from(shot.data, "base64"));
  ws.close();
})().catch((e) => { console.error("ERR", e); process.exit(1); });
