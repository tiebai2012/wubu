open("tools/shot_final.js","w",encoding="utf-8").write(r'''
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
  for (const [w,out] of JSON.parse(process.argv[3])) {
    await call("Emulation.setDeviceMetricsOverride",{width:w,height:200,deviceScaleFactor:1,mobile:false});
    await call("Page.navigate",{url:process.argv[2]});
    await sleep(6000);
    const s=await call("Page.captureScreenshot",{format:"png"});
    fs.writeFileSync(out,Buffer.from(s.data,"base64"));
    console.log(out, "ok");
  }
  ws.close();
})().catch(e=>{console.error("ERR",e);process.exit(1)});
''')
