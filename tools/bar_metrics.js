
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
  const out=[];
  for (const url of process.argv.slice(2)) {
    await call("Page.navigate",{url}); await sleep(4500);
    const r=await call("Runtime.evaluate",{expression:`(()=>{
      const q=s=>document.querySelector(s);
      const bx=el=>{if(!el)return null;const r=el.getBoundingClientRect();return [Math.round(r.x*10)/10,Math.round(r.y*10)/10,Math.round(r.width*10)/10,Math.round(r.height*10)/10]};
      const bar=q(".wubu-bar"), inner=q(".wubu-bar__inner"), logo=q(".wubu-bar__logo img"),
            title=q(".wubu-bar__title"), nav=q(".wubu-bar__nav"), cart=q(".wubu-bar__cart"),
            btn=q(".wubu-bar__top"), first=q(".wubu-bar__nav a");
      return {bar:bx(bar),inner:bx(inner),logo:bx(logo),title:bx(title),nav:bx(nav),
              first:bx(first),cart:bx(cart),btn:bx(btn),
              titleFS:title?getComputedStyle(title).fontSize:null,
              linkFS:first?getComputedStyle(first).fontSize:null,
              linkFW:first?getComputedStyle(first).fontWeight:null};
    })()`,returnByValue:true});
    out.push({page:url.split("/").pop(),...r.result.value});
  }
  console.log(JSON.stringify(out,null,1));
  fs.writeFileSync("tools/bar_metrics.json",JSON.stringify(out,null,1),"utf8");
  ws.close();
})().catch(e=>{console.error("ERR",e);process.exit(1)});
