// 打开本地购买页：加购两种规格，打开购物车，读出金额
const http = require("http");
const fs = require("fs");
function getJSON(url){return new Promise((res,rej)=>{http.get(url,r=>{let d="";r.on("data",c=>d+=c);r.on("end",()=>{try{res(JSON.parse(d))}catch(e){rej(e)}})}).on("error",rej)})}
function connect(url){return new Promise((res,rej)=>{const ws=new WebSocket(url);ws.onopen=()=>res(ws);ws.onerror=rej})}
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
  const list=await getJSON("http://127.0.0.1:9222/json/list");
  const t=list.find(x=>x.type==="page");
  const ws=await connect(t.webSocketDebuggerUrl);
  let id=0; const pend=new Map();
  ws.addEventListener("message",ev=>{const m=JSON.parse(ev.data); if(m.id&&pend.has(m.id)){const{res,rej}=pend.get(m.id);pend.delete(m.id);m.error?rej(new Error(JSON.stringify(m.error))):res(m.result)}});
  const call=(method,params)=>new Promise((res,rej)=>{const i=++id;pend.set(i,{res,rej});ws.send(JSON.stringify({id:i,method,params}))});
  await call("Page.enable",{}); await call("Runtime.enable",{});
  await call("Emulation.setDeviceMetricsOverride",{width:1410,height:900,deviceScaleFactor:1,mobile:false});
  ws.send(JSON.stringify({id:++id,method:"Page.navigate",params:{url:process.argv[2]}}));
  await sleep(7000);
  const r=await call("Runtime.evaluate",{expression:`(async()=>{
    const sleep=ms=>new Promise(r=>setTimeout(r,ms));
    const rows=document.querySelectorAll(".s-ecommerce-row-view-product");
    async function add(rowIdx, optIdx){
      const row=rows[rowIdx]; if(!row) return;
      const sel=row.querySelector("select");
      if(sel){const opts=Array.from(sel.options).filter(o=>o.value&&!o.disabled);const o=opts[optIdx]||opts[0];if(o){sel.value=o.value;sel.dispatchEvent(new Event("change",{bubbles:true}));}}
      const btn=row.querySelector(".s-ecommerce-row-view-product-order-btn"); if(btn) btn.click();
      await sleep(800);
    }
    await add(1,0);
    await add(0,1);
    const cart=document.querySelector(".s-shipping-cart-item"); if(cart) cart.click();
    await sleep(1500);
    const lines=[...document.querySelectorAll(".cart-item-wrapper")].map(el=>({
      name:(el.querySelector(".name")||{}).textContent,
      variant:(el.querySelector(".variation-name")||{}).textContent,
      price:(el.querySelector(".product-price")||{}).textContent,
      img:(el.querySelector(".image")||{}).style ? (el.querySelector(".image").style.backgroundImage||"").slice(0,60) : ""
    }));
    return { count:(document.querySelector(".item-number")||{}).textContent,
             lines, total:(document.querySelector(".shopping-footer .amount")||{}).textContent };
  })()`,awaitPromise:true,returnByValue:true});
  console.log(JSON.stringify(r.result.value,null,1));
  const shot=await call("Page.captureScreenshot",{format:"png"});
  fs.writeFileSync("_cart_real.png",Buffer.from(shot.data,"base64"));
  console.log("saved _cart_real.png");
  ws.close();
})().catch(e=>{console.error("ERR",e);process.exit(1)});
