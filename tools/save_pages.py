"""Save each page of wubu-pw.mysxl.cn as a standalone HTML file.

The platform's SPA re-renders by URL path, so an archived page opened as
"standards.html" would be rewritten into the home page. Removing the platform
scripts keeps the server-rendered markup (which is what the live site shows)
intact. Stylesheets stay linked to the CDN, so the pages keep their look.
"""
import os, re

RAW = "raw"
BASE = "https://wubu-pw.mysxl.cn"
ORIGINS = ("https://wubu-pw.mysxl.cn", "http://wubu-pw.mysxl.cn")

# 原站路径 -> 本地文件名
ROUTES = {"/": "index.html", "/2": "projects.html", "/3": "standards.html",
          "/4": "results.html", "/5": "about.html",
          "/pages/cookie-policy": BASE + "/pages/cookie-policy"}
PAGES = [("index.html", "index.html"), ("projects.html", "projects.html"),
         ("standards.html", "standards.html"), ("results.html", "results.html"),
         ("about.html", "about.html")]

SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.S | re.I)
SCRIPT_SELF_RE = re.compile(r"<script\b[^>]*/>", re.I)
ATTR_SRC = re.compile(r"""(\b(?:src|data-src)\s*=\s*)(['"])(/(?!/)[^'"]*)\2""", re.I)
ATTR_HREF = re.compile(r"""(\bhref\s*=\s*)(['"])([^'"]*)\2""", re.I)
PROTO_REL = re.compile(r"""(\b(?:src|href|data-src|poster|data-bg)\s*=\s*)(['"])//([^'"]+)\2""", re.I)
CSS_PROTO_REL = re.compile(r"""url\(\s*(['"]?)//([^'")]+)\1\s*\)""")
# 字体样式表写成 media="print" + onload 切换，没有脚本就永远不生效，这里直接改成 all
PRINT_LINK = re.compile(r"""(<link[^>]*?)\smedia=["']print["']([^>]*?)\sonload=["'][^"']*["']""", re.I)

APP_CSS = ('<link rel="stylesheet" href="https://static-assets.sxlcdn.com/'
           'application-2b688856817c0158ea671b54215a5d56a2f08ef76926fb7fb2e76f83ae02a5f6.css">')

# 购物车脚本要在每一页都加载：导航栏的角标数字靠它更新
SHOP_ASSETS = ""

# 原站的顶栏购物车是脚本渲染的，静态页里没有；这里按线上渲染结果原样补一份，
# 放在「回到顶部」按钮前面（每个导航条各一份，和线上一致）。
CART_NAV = (
    '<div class="s-icons"><ul class="s-nav-icons">'
    '<li class="s-nav-li shopping-cart-nav-container">'
    '<div class="s-nav-link-container">'
    '<div class="s-shipping-cart-item" title="您的购物车还是空的，赶快去挑选商品吧！" style="cursor: pointer;">'
    '<div id="s-ecommerce-shopping-cart" class="s-ecommerce-shopping-cart strikingly-fixed s-font-body">'
    '<div><i class="fa fa-shopping-cart"></i><span class="item-number">0</span></div>'
    '</div></div></div></li></ul></div>'
)
BACK_TO_TOP_OPEN = '<div class="s-nav-link-container s-nav-btn"'

# 原站顶栏默认是「透明 + 绝对定位」，白底与投影由脚本在滚动时切到另一个克隆条。
# 存档没有脚本，这里把白底固定下来，并给吸顶克隆条补上原站那套投影。
LOCAL_PAGES = ("index.html", "projects.html", "standards.html", "results.html", "about.html")
ANCHOR_RE = re.compile(r"<a\b[^>]*>", re.I)


def strip_internal_targets(html):
    """站内链接一律在当前标签页打开。"""
    def fix(m):
        tag = m.group(0)
        href = re.search(r"""\bhref\s*=\s*(['"])([^'"]*)\1""", tag, re.I)
        if not href:
            return tag
        url = href.group(2).split("#")[0].split("?")[0]
        if url.rsplit("/", 1)[-1] in LOCAL_PAGES:
            tag = re.sub(r"""\s+target\s*=\s*(['"])_blank\1""", "", tag, flags=re.I)
            tag = re.sub(r"""\s+rel\s*=\s*(['"])[^'"]*\1""", "", tag, flags=re.I)
        return tag
    return ANCHOR_RE.sub(fix, html)


def local_href(url):
    path, _, frag = url.partition("#")
    path = path.split("?")[0]
    if path in ROUTES:
        return ROUTES[path] + (("#" + frag) if frag else "")
    return None


report = []
for out_name, raw_name in PAGES:
    with open(os.path.join(RAW, raw_name), "rb") as f:
        html = f.read().decode("utf-8")

    html = SCRIPT_RE.sub("", html)
    html = SCRIPT_SELF_RE.sub("", html)

    # 站内相对资源（如 /dollars/.../show.js 已删除，图片等仍可能有）补全为绝对地址
    html = ATTR_SRC.sub(lambda m: m.group(1) + m.group(2) + BASE + m.group(3) + m.group(2), html)

    def href_fix(m):
        url = m.group(3)
        if not url or url.startswith(("mailto:", "tel:", "javascript:", "#")):
            return m.group(0)
        stripped = url
        for origin in ORIGINS:
            if stripped.startswith(origin):
                stripped = stripped[len(origin):] or "/"
                break
        if stripped.startswith("/") and not stripped.startswith("//"):
            target = local_href(stripped)
            return m.group(1) + m.group(2) + (target or (BASE + stripped)) + m.group(2)
        return m.group(0)

    html = ATTR_HREF.sub(href_fix, html)
    html = PROTO_REL.sub(lambda m: m.group(1) + m.group(2) + "https://" + m.group(3) + m.group(2), html)
    html = CSS_PROTO_REL.sub(lambda m: "url(%shttps://%s%s)" % (m.group(1), m.group(2), m.group(1)), html)
    html = strip_internal_targets(html)
    html = PRINT_LINK.sub(r'\1 media="all"\2', html)
    html = html.replace(BACK_TO_TOP_OPEN, CART_NAV + BACK_TO_TOP_OPEN)
    html = html.replace("</head>", APP_CSS + "\n</head>")
    # 导航高亮统一：各页都按首页那版显示（selected 固定落在“首页”），
    # 这样五个页面顶栏完全一致
    html = html.replace('<li class="s-nav-li selected">', '<li class="s-nav-li">')
    html = re.sub(r'(<li class="s-nav-li">)(\s*<div class="s-nav-link-container">\s*<a[^>]*href="index.html")',
                  r'<li class="s-nav-li selected">\2', html)


    with open(out_name, "wb") as f:
        f.write(html.encode("utf-8"))
    report.append((out_name, len(html)))

for name, size in report:
    print("%-16s %7d bytes" % (name, size))
