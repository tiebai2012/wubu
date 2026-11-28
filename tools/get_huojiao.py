import urllib.request, gzip, re
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
req=urllib.request.Request("https://mc.huojiao.fun", headers={"User-Agent":UA,"Accept-Encoding":"gzip"})
with urllib.request.urlopen(req, timeout=45) as r:
    b=r.read()
    if (r.headers.get("Content-Encoding") or "").lower()=="gzip": b=gzip.decompress(b)
s=b.decode("utf-8","replace")
open("tools/huojiao.html","w",encoding="utf-8").write(s)
print("字节:", len(s))
print("\n=== 导航结构 ===")
m=re.search(r'<(nav|header)[^>]*>.*?</\1>', s, re.S)
if m: print(m.group(0)[:900])
print("\n=== section id ===")
for mm in re.finditer(r'<section[^>]*id="([^"]*)"[^>]*>', s):
    print("  ", mm.group(0)[:100])
