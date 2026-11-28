// 手机宽度下点击 logo，验证新标签页跳转
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
  await call("Page.navigate", { url: process.argv[2] });
  await sleep(7000);

  const r = await call("Runtime.evaluate", {
    expression: `(() => {
      const links = [...document.querySelectorAll('a.wubu-logo-link')];
      const visible = links.filter(a => {
        const r = a.getBoundingClientRect();
        const cs = getComputedStyle(a);
        return r.width > 0 && r.height > 0 && cs.display !== 'none' && cs.visibility !== 'hidden';
      });
      const out = visible.map(a => {
        const r = a.getBoundingClientRect();
        const cx = Math.round(r.x + r.width/2), cy = Math.round(r.y + r.height/2);
        const top = document.elementFromPoint(cx, cy);
        return {href: a.href, target: a.getAttribute('target'),
                box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
                x: cx, y: cy,
                topInLink: top ? !!top.closest('a.wubu-logo-link') : false};
      });
      const broken = [...document.images].filter(im => im.complete && im.naturalWidth === 0).map(im => im.src.split('/').pop());
      return {total: links.length, visibleCount: visible.length, clickable: out, brokenImgs: broken};
    })()`,
    returnByValue: true
  });
  const info = r.result.value;
  console.log("总链接:", info.total, "| 可见可点:", info.visibleCount, "| 破图:", info.brokenImgs.length);
  info.clickable.forEach((c) => console.log("   ", JSON.stringify(c)));

  if (!info.clickable.length) { console.log("没有可点的 logo"); ws.close(); return; }

  const target = info.clickable[0];
  const before = (await call("Runtime.evaluate", { expression: "location.href", returnByValue: true })).result.value;
  for (const type of ["mousePressed", "mouseReleased"]) {
    await call("Input.dispatchMouseEvent", { type, x: target.x, y: target.y, button: "left", clickCount: 1 });
  }
  await sleep(3000);

  const pages = (await getJSON("http://127.0.0.1:9222/json/list"))
    .filter((x) => x.type === "page").map((x) => x.url);
  console.log("点击后打开:", pages.map((u) => u.slice(0, 70)));
  console.log(pages.some((u) => u.includes("huojiao.fun")) ? "结果：手机端 logo 跳转成功" : "结果：未跳转");

  const shot = await call("Page.captureScreenshot", { format: "png" });
  require("fs").writeFileSync("_mob_logo.png", Buffer.from(shot.data, "base64"));
  ws.close();
})().catch((e) => { console.error("ERR", e); process.exit(1); });
