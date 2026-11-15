// 抓包：在原站上加购 + 打开购物车，记录所有请求
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
  const target = list.find((t) => t.type === "page");
  const ws = await connect(target.webSocketDebuggerUrl);

  let id = 0;
  const pending = new Map();
  const requests = [];

  ws.addEventListener("message", (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
      return;
    }
    if (msg.method === "Network.requestWillBeSent") {
      const p = msg.params;
      requests.push({
        id: p.requestId,
        method: p.request.method,
        type: p.type,
        url: p.request.url,
        postData: p.request.postData || null
      });
    }
    if (msg.method === "Network.responseReceived") {
      const p = msg.params;
      const r = requests.find((x) => x.id === p.requestId);
      if (r) { r.status = p.response.status; r.mime = p.response.mimeType; }
    }
  });

  function call(method, params) {
    return new Promise((resolve, reject) => {
      const myId = ++id;
      pending.set(myId, { resolve, reject });
      ws.send(JSON.stringify({ id: myId, method, params }));
    });
  }

  await call("Page.enable", {});
  await call("Network.enable", {});
  await call("Network.setCacheDisabled", { cacheDisabled: true });
  await call("Page.navigate", { url: "http://wubu-pw.mysxl.cn/2" });
  await sleep(8000);

  // 选规格 + 加购
  const step1 = await call("Runtime.evaluate", {
    expression: `(async () => {
      const sleep = (ms) => new Promise(r => setTimeout(r, ms));
      const row = document.querySelector('.s-ecommerce-row-view-product');
      const sel = row && row.querySelector('select');
      if (sel) {
        const o = Array.from(sel.options).find(x => x.value && !x.disabled);
        if (o) { sel.value = o.value; sel.dispatchEvent(new Event('change', { bubbles: true })); }
      }
      const btn = row && row.querySelector('.s-ecommerce-row-view-product-order-btn');
      if (btn) btn.click();
      await sleep(2500);
      return { added: !!btn, variant: sel ? sel.value : null,
               number: (document.querySelector('.item-number')||{}).textContent };
    })()`,
    awaitPromise: true, returnByValue: true
  });
  console.log("step1:", JSON.stringify(step1.result.value));


  const step2 = await call("Runtime.evaluate", {
    expression: `(async () => {
      const sleep = (ms) => new Promise(r => setTimeout(r, ms));
      const cart = document.querySelector('.s-shipping-cart-item')
        || document.querySelector('#s-ecommerce-shopping-cart')
        || Array.from(document.querySelectorAll('a,div')).find(el => /购物车/.test(el.title || ''));
      if (cart) cart.click();
      await sleep(4000);
      return { clicked: !!cart, url: location.href };
    })()`,
    awaitPromise: true, returnByValue: true
  });
  console.log("step2:", JSON.stringify(step2.result.value));

  const interesting = requests.filter((r) =>
    ["XHR", "Fetch", "Document"].includes(r.type) ||
    /cart|checkout|order|shop|store|ecommerce|api|graphql/i.test(r.url)
  );

  const out = {
    total: requests.length,
    interesting: interesting.map((r) => ({
      method: r.method, type: r.type, status: r.status, mime: r.mime,
      url: r.url.slice(0, 220), post: r.postData ? r.postData.slice(0, 300) : null
    }))
  };
  fs.writeFileSync("tools/sniff.json", JSON.stringify(out, null, 1), "utf8");
  console.log("saved tools/sniff.json  total=" + out.total + " interesting=" + out.interesting.length);
  ws.close();
})().catch((e) => { console.error("ERR", e); process.exit(1); });
