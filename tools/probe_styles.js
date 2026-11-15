// 找出定义购物车面板样式的样式表
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
    expression: `(() => {
      const out = [];
      for (const ss of document.styleSheets) {
        let rules = null, err = null;
        try { rules = ss.cssRules; } catch (e) { err = String(e).slice(0, 80); }
        if (!rules) { out.push({ href: ss.href, error: err }); continue; }
        const txt = Array.from(rules).map(r => r.cssText || '').join('\\n');
        const hit = /s-kit-modal|shopping-cart-wrapper|cart-item-wrapper|buyer-checkout-dialog/.test(txt);
        out.push({
          href: ss.href || '(inline)',
          rules: rules.length,
          bytes: txt.length,
          hit
        });
      }
      return out;
    })()`,
    awaitPromise: true, returnByValue: true
  });
  console.log(JSON.stringify(res.result.value, null, 1));
  fs.writeFileSync("tools/stylesheets.json", JSON.stringify(res.result.value, null, 1), "utf8");
  ws.close();
})().catch((e) => { console.error("ERR", e); process.exit(1); });
