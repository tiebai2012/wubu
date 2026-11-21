"""把五个页面做成可以直接双击打开的离线站点。

做三件事，全部可重复执行（每次都从 raw/ 重新生成）：
  1. 站内导航链接 -> 本地文件（否则 /2、/3 这类路径在本地 404）
  2. 站外绝对地址里指向本站的 -> 本地文件
  3. 下载页面引用的图片、字体、样式、脚本到 assets/，并把地址改成相对路径
"""
import gzip, hashlib, os, re, shutil, ssl, urllib.request
from urllib.parse import urlsplit, unquote
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
ASSETS = os.path.join(ROOT, "assets")
SITE = "https://wubu-pw.mysxl.cn"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE

SOURCES = [
    ("index.html", "index.html"),
    ("2.html", "projects.html"),
    ("3.html", "standards.html"),
    ("4.html", "results.html"),
    ("5.html", "about.html"),
]
ROUTES = {"/": "index.html", "/2": "2.html", "/3": "3.html",
          "/4": "4.html", "/5": "5.html"}

EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".css", ".js",
       ".woff", ".woff2", ".ttf", ".eot", ".ico"}

manifest = {}       # url -> 本地相对路径
used_names = set()
lock_errors = []


def fetch(url, tries=2):
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA, "Accept-Encoding": "gzip",
                "Referer": SITE + "/",
            })
            with urllib.request.urlopen(req, timeout=45, context=CTX) as r:
                b = r.read()
                if (r.headers.get("Content-Encoding") or "").lower() == "gzip":
                    b = gzip.decompress(b)
                return b
        except Exception as e:  # noqa: BLE001
            last = e
    raise last


def local_name(url):
    sp = urlsplit(url)
    base = unquote(os.path.basename(sp.path)) or "index"
    stem, ext = os.path.splitext(base)
    if not ext:
        stem, ext = base, ".bin"
    # 同名不同图时用短哈希区分
    name = stem + ext
    if name in used_names:
        name = "%s-%s%s" % (stem, hashlib.md5(url.encode()).hexdigest()[:6], ext)
    used_names.add(name)
    return "assets/" + name


def download(url):
    if url in manifest:
        return manifest[url]
    data = fetch(url)
    rel = local_name(url)
    path = os.path.join(ROOT, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    manifest[url] = rel
    return rel


def absolute(url):
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        return SITE + url
    return url


# 匹配 src / href / data-src / srcset 里的地址
ATTR_RE = re.compile(r"""(<[a-zA-Z][^>]*?\s(?:src|href|data-src|data-bg)=)(['"])([^'"]*)\2""", re.I)
SRCSET_RE = re.compile(r"""(<img[^>]*?\ssrcset=)(['"])([^'"]*)\2""", re.I)
A_HREF_RE = re.compile(r"""(<a\b[^>]*?\bhref=)(['"])([^'"]*)\2""", re.I)
CSS_URL_RE = re.compile(r"""url\(\s*(['"]?)([^'")]+)\1\s*\)""")


def portrait_css():
    """窄屏适配样式：原站窄屏下图片网格溢出、首页标题被裁切。"""
    path = os.path.join(ROOT, "tools", "data", "portrait.css")
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return '<style id="portrait-fix">' + f.read() + "</style>"


def _safe(u):
    try:
        return download(u)
    except Exception as e:  # noqa: BLE001
        lock_errors.append((u, str(e)))
        return None


def main():
    if os.path.isdir(ASSETS):
        shutil.rmtree(ASSETS)
    os.makedirs(ASSETS, exist_ok=True)

    pages = {}
    for dst, src in SOURCES:
        with open(os.path.join(RAW, src), "rb") as f:
            pages[dst] = f.read().decode("utf-8")

    # 1+2：先收集需要下载的资源，同时把站内链接改掉
    to_download = set()
    for name, html in pages.items():
        # 站内导航链接
        def fix_a(m):
            head, q, url = m.group(1), m.group(2), m.group(3)
            path, _, frag = url.partition("#")
            frag = ("#" + frag) if frag else ""
            p = urlsplit(url)
            host = p.netloc or urlsplit(SITE).netloc
            path = p.path or "/"
            if host == urlsplit(SITE).netloc and path in ROUTES:
                return head + q + ROUTES[path] + frag + q
            return m.group(0)
        html = A_HREF_RE.sub(fix_a, html)

        # 指向本地页面的链接去掉 target=_blank
        def strip_target(m):
            tag = m.group(0)
            h = re.search(r'href=["\']([^"\']*)["\']', tag)
            if h and h.group(1).endswith(".html"):
                tag = re.sub(r"\s+target\s*=\s*([\"'])[^\"']*\1", "", tag)
            return tag
        html = re.sub(r"<a\b[^>]*>", strip_target, html, flags=re.I)

        # 资源地址：收集要下载的
        def collect(m):
            head, q, url = m.group(1), m.group(2), m.group(3)
            if not url or url.startswith(("#", "data:", "javascript:", "mailto:", "tel:")):
                return m.group(0)
            if url.startswith(("//", "http://", "https://")):
                absu = absolute(url)
                sp = urlsplit(absu)
                if sp.netloc.endswith(("sxlcdn.com", "sxlcdn.net", "strikingly.com", "typekit.net",
                                       ".cloudfront.net", "sxl.cn")):
                    to_download.add(absu)
            return m.group(0)
        ATTR_RE.sub(collect, html)
        pages[name] = html

    print("需要下载的资源：%d 个" % len(to_download))

    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(_safe, list(to_download)))

    print("下载成功：%d，失败：%d" % (len(manifest), len(lock_errors)))
    for u, e in lock_errors[:5]:
        print("  失败:", u[:80], e[:60])

    # 顶栏底色：原站白底由脚本在滚动时切换，file:// 下没有脚本会一直是透明
    NAV_CSS = ('<style id="offline-nav-bg">'
               '.s-navbar-desktop,.topBar{background-color:#fff !important;background-image:none !important;}'
               '</style>')

    # 3：改写资源地址为相对路径
    for name, html in pages.items():
        def rewrite(m):
            head, q, url = m.group(1), m.group(2), m.group(3)
            if not url or url.startswith(("#", "data:", "javascript:", "mailto:", "tel:")):
                return m.group(0)
            if url.startswith(("//", "http://", "https://")):
                local = manifest.get(absolute(url))
                if local:
                    return head + q + local + q
            return m.group(0)
        html = ATTR_RE.sub(rewrite, html)
        pages[name] = html

        html = html.replace("</head>", NAV_CSS + portrait_css() + "</head>", 1)

        with open(os.path.join(ROOT, name), "wb") as f:
            f.write(html.encode("utf-8"))

    # 4：样式表里的 url() 也要本地化
    css_files = [f for f in os.listdir(ASSETS) if f.endswith(".css")]
    css_done = 0
    for fn in css_files:
        path = os.path.join(ASSETS, fn)
        with open(path, "rb") as f:
            css = f.read().decode("utf-8", "replace")
        refs = [m.group(2) for m in CSS_URL_RE.finditer(css)
                if m.group(2).startswith(("//", "http")) and not m.group(2).startswith("data:")]
        changed = False
        for ref in refs:
            absu = absolute(ref)
            try:
                target = download(absu)
            except Exception:  # noqa: BLE001
                continue
            rel = os.path.relpath(os.path.join(ROOT, target), os.path.dirname(path)).replace(os.sep, "/")
            css = css.replace("url(%s)" % ref, "url(%s)" % rel)
            css = css.replace("url('%s')" % ref, "url('%s')" % rel)
            css = css.replace('url("%s")' % ref, 'url("%s")' % rel)
            changed = True
        if changed:
            with open(path, "wb") as f:
                f.write(css.encode("utf-8"))
            css_done += 1
    print("样式表本地化：%d 个" % css_done)

    print("\n已写入：", ", ".join(sorted(pages)))


if __name__ == "__main__":
    main()
