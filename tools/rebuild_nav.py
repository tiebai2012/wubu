"""重写顶部栏：删掉平台那套 s-nav（含两条克隆条），换成自己写的固定顶栏。

尺寸取自原站实测（1440 视口）：
  nav 1425×100；内容容器 1240 居中（左右各 92.5）；logo 127.6×60 @ (125,20)；
  站名 20px @ (268.7,37)；菜单 16px/700，链接内边距 10px 8px，首项 x=800；
  购物车图标 + 数字；回到顶部按钮 100×40 @ (1200,30)，圆角 4。
"""
import os, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIV_RE = re.compile(r"<div\b|</div\s*>", re.I)
NAV_RE = re.compile(r"""<div[^>]*class=["'][^"']*\bs-nav\b[^"']*["']""", re.I)

LOGO = ("https://user-assets.sxlcdn.com/images/1148093/FnJIeF8_NZ2B5b7E1G5Z3vK7rn7-.jpg"
        "?imageMogr2/strip/auto-orient/thumbnail/300x300%3E/quality/90!/interlace/1/format/jpeg")

PAGES = [
    ("index.html", "首页"),
    ("projects.html", "选择项目"),
    ("standards.html", "下载标准"),
    ("results.html", "历史评价成绩"),
    ("about.html", "关于五不"),
]


def bar(active):
    links = "\n".join(
        '      <a href="%s"%s>%s</a>' % (href, ' class="is-active"' if label == active else "", label)
        for href, label in PAGES
    )
    return f"""<header class="wubu-bar" id="wubu-bar">
  <div class="wubu-bar__inner">
    <a class="wubu-bar__logo" href="index.html" aria-label="五不评价协会">
      <img src="{LOGO}" alt="五不评价协会">
    </a>
    <div class="wubu-bar__title">五不评价协会成员网</div>
    <nav class="wubu-bar__nav" aria-label="主导航">
{links}
    </nav>
    <div class="wubu-bar__right">
      <span class="wubu-bar__cart" title="购物车"><i class="fa fa-shopping-cart" aria-hidden="true"></i><span class="wubu-bar__count">0</span></span>
      <a class="wubu-bar__top" href="#" data-to-top>回到顶部</a>
    </div>
  </div>
</header>
<style id="wubu-bar-css">
  .wubu-bar {{
    position: fixed; top: 0; left: 0; right: 0; z-index: 210;
    height: 100px; background: #fff;
  }}
  .wubu-bar.is-stuck {{ box-shadow: 0 1px rgba(0, 0, 0, 0.12); }}
  .wubu-bar, .wubu-bar * {{ box-sizing: border-box; }}
  .wubu-bar__inner {{
    width: 1240px; max-width: calc(100% - 40px); margin: 0 auto; padding: 0 32.5px;
    height: 100%; display: flex; align-items: center;
  }}
  .wubu-bar__logo img {{ display: block; height: 60px; width: auto; }}
  .wubu-bar__title {{
    margin-left: 16px; font-size: 20px; line-height: 26px; color: #000; white-space: nowrap;
  }}
  .wubu-bar__nav {{ margin-left: auto; display: flex; align-items: center; }}
  .wubu-bar__nav a {{
    display: inline-block; padding: 10px 8px; font-size: 16px; line-height: 18px;
    font-weight: 700; color: rgba(0, 0, 0, 0.8); white-space: nowrap;
  }}
  .wubu-bar__nav a:hover {{ color: #000; }}
  .wubu-bar__nav a.is-active {{ color: #000; box-shadow: inset 0 -1px 0 currentColor; }}
  .wubu-bar__right {{ margin-left: 20px; display: flex; align-items: center; gap: 14px; }}
  .wubu-bar__cart {{
    display: inline-flex; align-items: center; gap: 6px; color: #000;
    font-size: 16px; cursor: default;
  }}
  .wubu-bar__cart .fa {{ font-size: 18px; }}
  .wubu-bar__count {{ font-size: 16px; }}
  .wubu-bar__top {{
    display: inline-flex; align-items: center; justify-content: center;
    width: 100px; height: 40px; border-radius: 4px; background: #000; color: #fff;
    font-size: 16px; font-weight: 700; white-space: nowrap;
  }}
  .wubu-bar__top:hover {{ background: #2b2b2b; }}
  @media (max-width: 1120px) {{
    .wubu-bar__nav {{ margin-left: 24px; }}
    .wubu-bar__nav a {{ padding: 10px 6px; font-size: 15px; }}
  }}
  @media (max-width: 900px) {{
    .wubu-bar {{ height: 72px; }}
    .wubu-bar__logo img {{ height: 42px; }}
    .wubu-bar__title {{ font-size: 16px; margin-left: 12px; }}
    .wubu-bar__nav {{ display: none; }}
    .wubu-bar__top {{ width: auto; padding: 0 14px; height: 34px; font-size: 14px; }}
  }}
</style>
<script>
  (function () {{
    var bar = document.getElementById('wubu-bar');
    function onScroll() {{ bar.classList.toggle('is-stuck', window.scrollY > 60); }}
    window.addEventListener('scroll', onScroll, {{ passive: true }});
    onScroll();
    document.addEventListener('click', function (e) {{
      var t = e.target.closest('[data-to-top]');
      if (t) {{ e.preventDefault(); window.scrollTo({{ top: 0, behavior: 'smooth' }}); }}
    }});
  }})();
</script>
"""


def block_end(html, start):
    depth = 0
    for m in DIV_RE.finditer(html, start):
        depth += -1 if m.group(0).startswith("</") else 1
        if depth == 0:
            return m.end()
    return len(html)


def main():
    for path in sorted(glob.glob(os.path.join(ROOT, "*.html"))):
        name = os.path.basename(path)
        active = next((label for href, label in PAGES if href == name), None)
        if active is None:
            continue
        with open(path, "rb") as f:
            html = f.read().decode("utf-8")

        # 删掉旧的平台导航（含正常条与克隆条）
        while True:
            m = NAV_RE.search(html)
            if not m:
                break
            end = block_end(html, m.start())
            html = html[:m.start()] + html[end:]

        # 插到 <body ...> 之后
        b = re.search(r"<body[^>]*>", html, re.I)
        if not b:
            print("%-16s 没找到 body" % name)
            continue
        html = html[:b.end()] + "\n" + bar(active) + html[b.end():]

        with open(path, "wb") as f:
            f.write(html.encode("utf-8"))
        print("%-16s 顶栏已重写（当前页：%s）" % (name, active))


if __name__ == "__main__":
    main()
