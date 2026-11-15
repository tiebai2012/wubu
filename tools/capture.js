// CDP：打开页面，分别在顶部与滚动后截图，并读出导航状态
// 用法: node capture.js <url> <outPrefix> [scroll]
const http = require("http");
const fs = require("fs");

const URL_ = process.argv[2];
const PREFIX = process.argv[3] || "cap";
const SCROLL = Number(process.argv[4] || 700);
const W = 1410, H = 900;

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
  await call("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: 1, mobile: false });
  await call("Page.navigate", { url: URL_ });
  await sleep(8000);

  async function shot(name) {
    const s = await call("Page.captureScreenshot", { format: "png" });
    fs.writeFileSync(name, Buffer.from(s.data, "base64"));
  }
  await shot(PREFIX + "-top.png");

  const info = await call("Runtime.evaluate", {
    expression: `(async () => {
      window.scrollTo(0, ${SCROLL});
      await new Promise(r => setTimeout(r, 1800));
      const nav = document.querySelector('.s-navbar-desktop-normal');
      const clone = document.querySelector('.static-stuck') || document.querySelector('.s-navbar-desktop-fixed._show');
      const cs = nav ? getComputedStyle(nav) : null;
      const r = nav ? nav.getBoundingClientRect() : null;
      const rc = clone ? clone.getBoundingClientRect() : null;
      return {
        scrollY: window.scrollY,
        navPos: cs ? cs.position : null,
        navShadow: cs ? cs.boxShadow : null,
        navRect: r ? [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] : null,
        cloneRect: rc ? [Math.round(rc.x), Math.round(rc.y), Math.round(rc.width), Math.round(rc.height)] : null
      };
    })()`,
    awaitPromise: true, returnByValue: true
  });
  console.log(JSON.stringify(info.result.value, null, 1));
  await shot(PREFIX + "-scrolled.png");
  ws.close();
})().catch((e) => { console.error("ERR", e); process.exit(1); });
