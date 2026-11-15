"""把整站爬一遍：从首页与 sitemap 出发，收集所有站内页面并记录标题、支付相关字样。"""
import gzip, json, re, ssl, sys, urllib.request
from urllib.parse import urljoin, urlsplit
from lxml import html as LH

BASE = "https://wubu-pw.mysxl.cn"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
seen, queue, pages = set(), ["/", "/2", "/3", "/4", "/5", "/pages/cookie-policy"], []
SKIP = re.compile(r"\.(png|jpe?g|gif|svg|webp|css|js|ico|woff2?|ttf|pdf|zip)$", re.I)


def fetch(path):
    url = urljoin(BASE + "/", path)
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept-Encoding": "gzip", "Accept-Language": "zh-CN,zh;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=45, context=ctx) as r:
        b = r.read()
        if (r.headers.get("Content-Encoding") or "").lower() == "gzip":
            b = gzip.decompress(b)
        return r.geturl(), r.status, b


# sitemap / robots
for probe in ("/sitemap.xml", "/robots.txt"):
    try:
        u, st, body = fetch(probe)
        txt = body.decode("utf-8", "replace")
        print("== %s (%s) ==" % (probe, st))
        print(txt[:600])
        for m in re.finditer(r"<loc>\s*([^<\s]+)\s*</loc>", txt):
            p = urlsplit(m.group(1)).path or "/"
            if p not in queue:
                queue.append(p)
    except Exception as e:  # noqa: BLE001
        print("== %s -> %s" % (probe, e))

while queue and len(pages) < 40:
    path = queue.pop(0)
    if path in seen or SKIP.search(path):
        continue
    seen.add(path)
    try:
        final, status, body = fetch(path)
    except Exception as e:  # noqa: BLE001
        pages.append({"path": path, "status": "ERR", "error": str(e)[:80]})
        continue
    doc = LH.fromstring(body.decode("utf-8", "replace"))
    title = (doc.findtext(".//title") or "").strip()
    text = " ".join(doc.body.text_content().split()) if doc.body is not None else ""
    hits = [w for w in ("微信", "支付宝", "支付", "收款", "转账", "付款", "银行卡") if w in text]
    pages.append({
        "path": path, "status": status, "title": title,
        "bytes": len(body), "paywords": hits,
        "sample": text[:160],
    })
    for a in doc.xpath("//a[@href]"):
        href = a.get("href") or ""
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        p = urlsplit(urljoin(BASE + path, href))
        if p.netloc and p.netloc != urlsplit(BASE).netloc:
            continue
        if p.path and p.path not in seen and not SKIP.search(p.path):
            queue.append(p.path)

json.dump(pages, open("raw/site_crawl.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n== 共 %d 个页面 ==" % len(pages))
for p in pages:
    flag = ",".join(p.get("paywords") or []) or "-"
    print("%-28s %-4s %-42s %s" % (p["path"][:28], p["status"], p.get("title", "")[:40], flag))
