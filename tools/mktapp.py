open("tools/test_app.js","w",encoding="utf-8").write(r'''
const http=require("http"),fs=require("fs");
function getJSON(u){return new Promise((res,rej)=>{http.get(u,r=>{let d="";r.on("data",c=>d+=c);r.on("end",()=>{try{res(JSON.parse(d))}catch(e){rej(e)}})}).on("error",rej)})}
function connect(u){return new Promise((res,rej)=>{const ws=new WebSocket(u);ws.onopen=()=>res(ws);ws.onerror=rej})}
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
  const list=await getJSON("http://127.0.0.1:9222/json/list");
  const t=list.find(x=>x.type==="page");
  const ws=await connect(t.webSocketDebuggerUrl);
  let id=0;const pend=new Map();
  ws.addEventListener("message",ev=>{const m=JSON.parse(ev.data);if(m.id&&pend.has(m.id)){const{res,rej}=pend.get(m.id);pend.delete(m.id);m.error?rej(new Error(JSON.stringify(m.error))):res(m.result)}});
  const call=(method,params)=>new Promise((res,rej)=>{const i=++id;pend.set(i,{res,rej});ws.send(JSON.stringify({id:i,method,params}))});
  await call("Page.enable",{});await call("Runtime.enable",{});
  await call("Emulation.setDeviceMetricsOverride",{width:1440,height:900,deviceScaleFactor:1,mobile:false});
  await call("Page.navigate",{url:process.argv[2]});await sleep(7000);
  const r=await call("Runtime.evaluate",{expression:`(async()=>{
    const sleep=ms=>new Promise(r=>setTimeout(r,ms));
    const out=[];
    const links=[...document.querySelectorAll('a[href^="#p-"]')].slice(0,5);
    for (const a of links) {
      a.click(); await sleep(700);
      const active=[...document.querySelectorAll('.slide.is-page-active')]
        .map(el=>(el.className||'').match(/s-section-\d+|s-page-\d+/)?.[0]||'?');
      out.push({clicked:a.getAttribute('href'), text:a.textContent.trim().slice(0,8),
                active, url: location.hash, scrollY: Math.round(window.scrollY),
                visibleSlides:[...document.querySelectorAll('.slide')].filter(el=>getComputedStyle(el).display!=='none').length});
    }
    return out;
  })()`,awaitPromise:true,returnByValue:true});
  console.log(JSON.stringify(r.result.value,null,1));
  ws.close();
})().catch(e=>{console.error("ERR",e);process.exit(1)});
''')
