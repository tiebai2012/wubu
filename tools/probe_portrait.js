// 竖屏下量各页的实际溢出元素和宽度
const http = require("http");

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
  await call("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });

  for (const url of process.argv.slice(2)) {
    await call("Page.navigate", { url });
    await sleep(4500);
    const r = await call("Runtime.evaluate", {
      expression: `(() => {
        const vw = document.documentElement.clientWidth;
        const docW = document.documentElement.scrollWidth;
        const wide = [];
        document.querySelectorAll('body *').forEach(el => {
          const r = el.getBoundingClientRect();
          if (r.width > vw + 1 || r.right > vw + 2) {
            const cls = (el.className || '').toString().slice(0, 46);
            wide.push({tag: el.tagName, cls, w: Math.round(r.width), right: Math.round(r.right),
                       fs: getComputedStyle(el).fontSize});
          }
        });
        // 只留最外层几项
        return {vw, docW, overflow: wide.slice(0, 8)};
      })()`,
      returnByValue: true
    });
    console.log(url.split("/").pop(), JSON.stringify(r.result.value));
  }
  ws.close();
})().catch((e) => { console.error("ERR", e); process.exit(1); });
