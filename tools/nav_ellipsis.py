"""桌面端导航「…」折叠：直接复用原站自带的 .s-nav-ellipsis 元素。

原站的每组导航里本来就带一个折叠项：
  <li class="s-nav-li s-nav-ellipsis hidden s-navbar-dropdown _down">
    <span class="s-font-body s-nav-dropdown-text">
      <i class="ellipsis-icon">… </i><i class="fa drop-down-icon-bold fas fa-chevron-down"></i>
    </span>
    <ul class="s-collapsed-nav"> … 全部菜单项 … </ul>
  </li>
平台脚本负责去掉 hidden 类、按窗口宽度折叠前面的项。这里只补这一步逻辑，
不再自造按钮和面板，外观完全沿用原站样式表。

实测阈值：≥1150 全部显示；1050–1149 显示前 4 项；<1050 显示前 3 项。
"""
import os, glob, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JS = """
<script>
(function () {
  function boot() {
    var lists = Array.prototype.slice.call(document.querySelectorAll('.s-uncollapsed-nav'));
    lists.forEach(function (ul) {
      var items = Array.prototype.slice.call(ul.children).filter(function (li) {
        return !li.classList.contains('s-nav-ellipsis') && li.querySelector('.s-nav-link-container');
      });
      // 原站每组里还带一份重复项，只取前 5 个真菜单项
      items = items.slice(0, 5);
      var ell = ul.querySelector('.s-nav-ellipsis');
      if (!ell || items.length < 4) return;

      var dropdown = ell.querySelector('.s-collapsed-nav');

      function apply(n) {
        items.forEach(function (li, i) {
          li.style.setProperty('display', i < n ? 'inline-block' : 'none', 'important');
        });
        var hidden = n < items.length;
        ell.classList.toggle('hidden', !hidden);
        ell.style.setProperty('display', hidden ? 'inline-block' : 'none', 'important');

        // 下拉里只留被收起的项
        if (dropdown) {
          Array.prototype.slice.call(dropdown.children).forEach(function (li, i) {
            li.style.setProperty('display', i >= n ? '' : 'none', 'important');
          });
        }
      }

      function pick() {
        var w = window.innerWidth, n;
        if (w >= 1150) n = 5;
        else if (w >= 1050) n = 4;
        else n = 3;
        apply(Math.min(n, items.length));
      }

      pick();
      window.addEventListener('resize', function () {
        clearTimeout(ul._t);
        ul._t = setTimeout(pick, 100);
      });

      // 原站下拉由 hover 展开；补一个点击切换，触屏也能用
      ell.addEventListener('click', function (e) {
        if (e.target.closest('a')) return;
        ell.classList.toggle('_open');
      });
      document.addEventListener('click', function (e) {
        if (!ell.contains(e.target)) ell.classList.remove('_open');
      });
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
</script>
"""

CSS = """<style id="nav-ellipsis-css">
/* 让原站自带的折叠下拉可点开（原站只有 hover） */
.s-nav-ellipsis._open > .s-collapsed-nav { display: block !important; }
.s-nav-ellipsis._open .drop-down-icon-bold { transform: rotate(180deg); }
/* 窄屏手机用抽屉，不用折叠菜单 */
@media (max-width: 767px) {
  .s-nav-ellipsis { display: none !important; }
}
</style>
"""


def main():
    for path in sorted(glob.glob(os.path.join(ROOT, "*.html"))):
        name = os.path.basename(path)
        if name == "app.html":
            continue
        with open(path, "rb") as f:
            html = f.read().decode("utf-8")

        html = _strip_old(html)
        if "s-uncollapsed-nav" not in html:
            print("%-12s 没有桌面导航" % name)
            continue

        html = html.replace("</head>", CSS + "</head>", 1)
        html = html.replace("</body>", JS + "</body>", 1)

        with open(path, "wb") as f:
            f.write(html.encode("utf-8"))
        print("%-12s 已接入原站折叠菜单" % name)


def _strip_old(html):
    html = re.sub(r'<style id="nav-ellipsis-css">.*?</style>\n?', "", html, flags=re.S)
    html = re.sub(r"<script>\s*\(function \(\) \{\s*function boot\(\) \{\s*var lists = Array\.prototype\.slice\.call\(document\.querySelectorAll\('\.s-uncollapsed-nav'\)\);.*?</script>", "", html, flags=re.S)
    return html


if __name__ == "__main__":
    main()
