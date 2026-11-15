import urllib.request, ssl, os, sys
BASE="http://wubu-pw.mysxl.cn"
PAGES={"/":"index","/2":"projects","/3":"standards","/4":"results","/5":"about"}
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
for path,name in PAGES.items():
    req=urllib.request.Request(BASE+path, headers={"User-Agent":UA,"Accept-Encoding":"gzip"})
    with urllib.request.urlopen(req, timeout=45, context=ctx) as r:
        b=r.read()
        if (r.headers.get("Content-Encoding") or "").lower()=="gzip": import gzip; b=gzip.decompress(b)
    open(os.path.join("raw",name+".html"),"wb").write(b)
    print("OK", path, name, len(b))
