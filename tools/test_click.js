// 真实点击 logo，验证是否在新标签页打开主站（可用于任意 URL / 子路径）
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
  await call("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await call("Page.navigate", { url: process.argv[2] });
  await sleep(7000);

  const r = await call("Runtime.evaluate", {
    expression: `(() => {
      const a = [...document.querySelectorAll('a.wubu-logo-link')].find(x => x.getBoundingClientRect().width > 0);
      const broken = [...document.images].filter(im => im.complete && im.naturalWidth === 0).map(im => im.src.split('/').pop());
      if (!a) return {found: false, total: document.querySelectorAll('a.wubu-logo-link').length, brokenImgs: broken};
      const rect = a.getBoundingClientRect();
      const cx = Math.round(rect.x + rect.width/2), cy = Math.round(rect.y + rect.height/2);
      const top = document.elementFromPoint(cx, cy);
      return {found: true, href: a.href, target: a.getAttribute('target'),
              box: [Math.round(rect.x), Math.round(rect.y), Math.round(rect.width), Math.round(rect.height)],
              x: cx, y: cy,
              topTag: top ? top.tagName : null,
              topInLink: top ? !!top.closest('a.wubu-logo-link') : false,
              brokenImgs: broken};
    })()`,
    returnByValue: true
  });
  const info = r.result.value;
  console.log("logo:", JSON.stringify(info));

  if (!info.found) { ws.close(); return; }

  const before = (await call("Runtime.evaluate", { expression: "location.href", returnByValue: true })).result.value;
  for (const type of ["mousePressed", "mouseReleased"]) {
    await call("Input.dispatchMouseEvent", { type, x: info.x, y: info.y, button: "left", clickCount: 1 });
  }
  await sleep(3000);
  const after = (await call("Runtime.evaluate", { expression: "location.href", returnByValue: true })).result.value;
  console.log("当前页 点击前:", before);
  console.log("当前页 点击后:", after);

  const targets = await getJSON("http://127.0.0.1:9222/json/list");
  const pages = targets.filter((x) => x.type === "page").map((x) => x.url);
  console.log("打开的页面:");
  pages.forEach((u) => console.log("   ", u.slice(0, 90)));
  console.log(pages.some((u) => u.includes("huojiao.fun")) ? "结果：已新开 huojiao.fun" : "结果：未新开");

  ws.close();
})().catch((e) => { console.error("ERR", e); process.exit(1); });
