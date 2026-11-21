"""手机端导航 + 删除页脚。

1. 原站在移动端左上角有个三条杠按钮，点开是抽屉式导航；本地版没有平台脚本，
   这里补一套等价实现（按钮 + 抽屉 + 遮罩，纯 CSS/JS，不依赖平台）。
2. 删除每页底部的「关于我们 / 我们的使命 / 正在招聘！/ 资源 / 教程 / 品牌资料 /
   联系我们 / 321-555-5555 / info@company.com」整块页脚。
"""
import os, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "tools", "data")

PAGES = [
    ("index.html", "首页"),
    ("2.html", "选择项目"),
    ("3.html", "下载标准"),
    ("4.html", "历史评价成绩"),
    ("5.html", "关于五不"),
]

DIV_RE = re.compile(r"<div\b|</div\s*>", re.I)
FOOT_RE = re.compile(r"""<div[^>]*class=["'][^"']*s-footer-section[^"']*["']""", re.I)


def block_end(html, start):
    depth = 0
    for m in DIV_RE.finditer(html, start):
        depth += -1 if m.group(0).startswith("</") else 1
        if depth == 0:
            return m.end()
    return len(html)


def menu_html(active):
    items = "\n".join(
        '      <li><a href="%s"%s>%s</a></li>'
        % (href, ' class="is-active"' if label == active else "", label)
        for href, label in PAGES
    )
    return f"""<button class="m-nav-toggle" id="m-nav-toggle" type="button"
        aria-label="打开导航菜单" aria-expanded="false" aria-controls="m-nav-drawer">
  <span></span><span></span><span></span>
</button>
<div class="m-nav-mask" id="m-nav-mask"></div>
<nav class="m-nav-drawer" id="m-nav-drawer" aria-label="移动端导航">
  <ul>
{items}
  </ul>
</nav>
<script>
  (function () {{
    var btn = document.getElementById('m-nav-toggle');
    var drawer = document.getElementById('m-nav-drawer');
    var mask = document.getElementById('m-nav-mask');
    if (!btn || !drawer) return;
    function set(open) {{
      btn.classList.toggle('is-open', open);
      drawer.classList.toggle('is-open', open);
      mask.classList.toggle('is-open', open);
      document.body.classList.toggle('m-nav-locked', open);
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    }}
    btn.addEventListener('click', function () {{
      set(!drawer.classList.contains('is-open'));
    }});
    mask.addEventListener('click', function () {{ set(false); }});
    document.addEventListener('keydown', function (e) {{
      if (e.key === 'Escape') set(false);
    }});
    drawer.addEventListener('click', function (e) {{
      if (e.target.tagName === 'A') set(false);
    }});
  }})();
</script>
"""


def main():
    with open(os.path.join(DATA, "mobile-menu.css"), encoding="utf-8") as f:
        css = f.read()

    for path in sorted(glob.glob(os.path.join(ROOT, "*.html"))):
        name = os.path.basename(path)
        active = next((label for href, label in PAGES if href == name), None)
        if active is None:
            continue
        with open(path, "rb") as f:
            html = f.read().decode("utf-8")

        # --- 1. 删页脚 ---
        removed = 0
        while True:
            m = FOOT_RE.search(html)
            if not m:
                break
            end = block_end(html, m.start())
            removed += end - m.start()
            html = html[:m.start()] + html[end:]
        # 外面那层空容器一并去掉
        html = re.sub(r"""<div[^>]*id=["']s-footer-section-container["'][^>]*>\s*</div>""",
                      "", html, flags=re.I)

        # --- 2. 手机端导航 ---
        if 'id="m-nav-toggle"' not in html:
            b = re.search(r"<body[^>]*>", html, re.I)
            html = html[:b.end()] + "\n" + menu_html(active) + html[b.end():]
            html = html.replace("</head>", "<style id=\"m-nav-css\">\n" + css + "</style>\n</head>", 1)

        with open(path, "wb") as f:
            f.write(html.encode("utf-8"))
        print("%-12s 删除页脚 %5d 字节，手机菜单已加入" % (name, removed))


if __name__ == "__main__":
    main()
