import json, gzip, ssl, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE

def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers={
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://wubu-pw.mysxl.cn/2",
    })
    with urllib.request.urlopen(req, timeout=45, context=ctx) as r:
        b = r.read()
        if (r.headers.get("Content-Encoding") or "").lower() == "gzip":
            b = gzip.decompress(b)
        return b.decode("utf-8")

out = {}
out["products"] = json.loads(get("https://wubu-pw.mysxl.cn/r/v1/sites/12725085/products?per=20&page=1&need_filter_options=true"))
out["ecommerce"] = json.loads(get("https://wubu-pw.mysxl.cn/r/v1/sites/12725085/ecommerce"))
json.dump(out, open("raw/api_products.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

p = out["products"]
print("keys:", list(p.keys())[:8])
items = p.get("data") or p.get("products") or []
print("products:", len(items))
for it in items:
    print("\n-", it.get("name"))
    for k in ("id", "price", "min_price", "max_price", "currency", "sku"):
        if k in it: print("   ", k, "=", it[k])
    opts = it.get("options") or it.get("variations") or []
    print("    options:", json.dumps(opts, ensure_ascii=False)[:600])
