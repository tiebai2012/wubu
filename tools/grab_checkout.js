// 抓原站「下单结算」弹出的结算弹窗（结构 + 相关 CSS）
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
      const checkout = document.querySelector('.checkout-btn');
      if (checkout) checkout.click();
      await sleep(4000);

      const panel = Array.from(document.querySelectorAll('.s-kit-modal'))
        .filter(el => /结算|付款方式|订单摘要/.test(el.textContent || ''))
        .sort((a, b) => a.getBoundingClientRect().width * a.getBoundingClientRect().height -
                        b.getBoundingClientRect().width * b.getBoundingClientRect().height)[0];
      if (!panel) return { found: false };

      const r = panel.getBoundingClientRect();
      // 抓这个面板用到的全部 CSS 规则
      const keys = ['buyer-checkout-dialog','checkout-','payment','shipping','order-','modal','form-item',
                    'address','contact','leave-message','freight','purchase'];
      const seen = new Set(), picked = [];
      for (const ss of document.styleSheets) {
        let rules = null;
        try { rules = ss.cssRules; } catch (e) { continue; }
        if (!rules) continue;
        for (const rule of rules) {
          const txt = rule.cssText || '';
          if (!txt || seen.has(txt)) continue;
          if (keys.some(k => txt.includes(k))) { seen.add(txt); picked.push(txt); }
        }
      }
      return {
        found: true,
        cls: (panel.className || '').toString(),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        html: panel.outerHTML,
        css: picked.join('\\n'),
        cssCount: picked.length,
        wrapperHtml: (panel.parentElement ? panel.parentElement.outerHTML.slice(0, 400) : '')
      };
    })()`,
    awaitPromise: true, returnByValue: true
  });

  const v = res.result.value;
  if (!v || !v.found) {
    console.log("NOT FOUND", JSON.stringify(v));
  } else {
    fs.writeFileSync("raw/checkout-panel.html", v.html, "utf8");
    fs.writeFileSync("raw/checkout-panel.css", v.css, "utf8");
    console.log(JSON.stringify({ cls: v.cls, rect: v.rect, html: v.html.length, css: v.css.length, rules: v.cssCount }, null, 1));
  }
  const shot = await call("Page.captureScreenshot", { format: "png" });
  fs.writeFileSync("raw/checkout-panel.png", Buffer.from(shot.data, "base64"));
  ws.close();
})().catch((e) => { console.error("ERR", e); process.exit(1); });
