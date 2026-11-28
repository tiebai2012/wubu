"""把五个页面合并成一个 app.html：右上角导航切换的是页面内的区块，不跳转。

做法：
  - 取 2.html（选择项目）作为外壳，保留它的导航、脚本、样式
  - 把 index / 3 / 4 / 5 的页面主体（page-wrapper 里的 slides）合并进来
  - 导航链接改成 #index / #2 / #3 / #4 / #5，点击切页由一小段脚本完成
  - 每个页面原有的样式块都已经在同一份 HTML 里，不需要额外处理
"""
import os, re, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = [
    ("index", "index.html", "首页"),
    ("2", "2.html", "选择项目"),
    ("3", "3.html", "下载标准"),
    ("4", "4.html", "历史评价成绩"),
    ("5", "5.html", "关于五不"),
]
SHELL = "2.html"


def extract_slides(html):
    """取出页面主体：<ul class="slides ..."> ... </ul>"""
    m = re.search(r'<ul\b[^>]*class="[^"]*\bslides\b[^"]*"[^>]*>', html)
    if not m:
        return None
    start = m.start()
    depth = 0
    for mm in re.finditer(r"<ul\b|</ul\s*>", html[start:]):
        if mm.group(0).startswith("</"):
            depth -= 1
        else:
            depth += 1
        if depth == 0:
            return html[start:start + mm.end()]
    return None


def main():
    pages = {}
    for key, name, label in PAGES:
        with open(os.path.join(ROOT, name), encoding="utf-8") as f:
            pages[key] = f.read()

    shell = pages["2"]
    shell_slides = extract_slides(shell)
    if not shell_slides:
        raise SystemExit("在 %s 里找不到页面主体" % SHELL)

    # 其它页的 slides 也合并进来（去掉各自的 page-N 类里的页面编号）
    extra = []
    for key, name, label in PAGES:
        if key == "2":
            continue
        sl = extract_slides(pages[key])
        if not sl:
            print("跳过 %s" % name)
            continue
        extra.append(sl)

    def tag(slides_html, key):
        # 给这段 slides 里的每个 <li class="slide ..."> 标上 data-page
        return re.sub(r'<li class="(slide[^"]*)"',
                      lambda m: '<li class="%s" data-page="%s"' % (m.group(1), key),
                      slides_html)

    combined = tag(shell_slides, "2") + "\n" + "\n".join(
        tag(sl, k) for sl, (k, _, _) in zip(extra, [p for p in PAGES if p[0] != "2"])
    )

    # 外壳里替换掉原来的 slides
    out = shell.replace(shell_slides, combined, 1)

    # 导航链接改成本页锚点
    link_map = {f"{k}.html": f"#p-{k}" for k, _, _ in PAGES}
    for old, new in link_map.items():
        out = out.replace('href="%s"' % old, 'href="%s"' % new)

    # 加载/切换脚本
    switcher = """
<style id="spa-css">
  /* 一次只显示一个页面的 slides 列表 */
  ul.slides { display: none !important; }
  ul.slides.is-page-active { display: block !important; }
</style>
<script>
(function () {
  function boot() {
    var lists = Array.prototype.slice.call(document.querySelectorAll('ul.slides'));
    if (!lists.length) return;

    var order = ['index', '2', '3', '4', '5'];
    function keyOf(ul) {
      var cls = ul.className || '';
      var m = /s-page-([0-9]+)/.exec(cls);
      if (m) return m[1] === '1' ? 'index' : m[1];
      return 'index';
    }

    function show(key) {
      lists.forEach(function (ul) {
        ul.classList.toggle('is-page-active', keyOf(ul) === key);
      });
      window.scrollTo(0, 0);
    }

    function fromHash() {
      var h = (location.hash || '').replace('#p-', '');
      show(order.indexOf(h) >= 0 ? h : 'index');
    }

    document.addEventListener('click', function (e) {
      var a = e.target.closest('a[href^="#p-"]');
      if (!a) return;
      e.preventDefault();
      location.hash = a.getAttribute('href');
    });
    window.addEventListener('hashchange', fromHash);
    fromHash();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
</script>
"""
"""
    out = out.replace("</body>", switcher + "</body>", 1)

    with open(os.path.join(ROOT, "app.html"), "w", encoding="utf-8") as f:
        f.write(out)
    print("已生成 app.html：%d 字节，合并 %d 个页面主体" % (len(out.encode("utf-8")), len(pages)))


if __name__ == "__main__":
    main()
