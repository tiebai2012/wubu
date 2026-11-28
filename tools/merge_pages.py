"""把五个页面合并成一个 app.html：多页面内容放在同一个文件里，导航切换不跳转。

结构参考 mc.huojiao.fun 的单页形式：一个 HTML 里有多组页面内容，
点击导航只切换显示哪一组，地址栏用 #p-xxx 记录。

实现要点：
  原站每个页面各有一个 <ul class="slides s-page-N">，内部由平台轮播脚本接管。
  合并后保留全部 5 个 slides 列表，用一段脚本控制「只显示当前页那一组」，
  并把平台轮播可能覆盖的显示状态用行内 important 锁住。
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = [
    ("index", "index.html", "首页"),
    ("2", "2.html", "选择项目"),
    ("3", "3.html", "下载标准"),
    ("4", "4.html", "历史评价成绩"),
    ("5", "5.html", "关于五不"),
]
SHELL = "2.html"

SLIDES_OPEN = re.compile(r'<ul\b[^>]*class="[^"]*\bslides\b[^"]*"[^>]*>')


def find_slides_span(html):
    """返回 (start, end)：整个 <ul class=slides> ... </ul> 的范围。"""
    m = SLIDES_OPEN.search(html)
    if not m:
        return None
    start = m.start()
    depth = 0
    for mm in re.finditer(r"<ul\b|</ul\s*>", html[start:]):
        depth += -1 if mm.group(0).startswith("</") else 1
        if depth == 0:
            return start, start + mm.end()
    return None


SWITCHER = """
<style id="spa-css">
  /* 合并后由脚本决定显示哪一页 */
  #spa-host > ul.slides { display: block !important; }
</style>
<script>
(function () {
  var ORDER = ['index', '2', '3', '4', '5'];
  var store = {};        // 每一页的 slides HTML
  var host = null;

  function keyOf(ul) {
    var m = /s-page-([0-9]+)/.exec(ul.className || '');
    if (!m) return 'index';
    return m[1] === '1' ? 'index' : m[1];
  }

  function boot() {
    var lists = Array.prototype.slice.call(document.querySelectorAll('ul.slides'));
    if (!lists.length) return;

    // 记下每页的完整 HTML，然后把它们从 DOM 里摘掉
    lists.forEach(function (ul) {
      store[keyOf(ul)] = ul.outerHTML;
      var wrap = ul.parentElement;
      ul.remove();
      if (wrap && wrap.classList.contains('page-wrapper')) {
        if (!host) host = wrap;
      }
    });
    if (!host) host = document.body;

    function show(key) {
      if (ORDER.indexOf(key) < 0) key = 'index';
      host.innerHTML = store[key] || store['index'] || '';
      // 让新插入的 slides 接管布局
      var ul = host.querySelector('ul.slides');
      if (ul) {
        ul.style.setProperty('display', 'block', 'important');
        ['slick-initialized', 'slick-slider'].forEach(function (c) { ul.classList.remove(c); });
      }
      window.scrollTo(0, 0);
    }

    function fromHash() {
      show((location.hash || '').replace('#p-', ''));
    }

    document.addEventListener('click', function (e) {
      var a = e.target.closest('a[href^="#p-"]');
      if (!a) return;
      e.preventDefault();
      var k = a.getAttribute('href').replace('#p-', '');
      if (location.hash === '#p-' + k) { show(k); } else { location.hash = '#p-' + k; }
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


def main():
    bodies = {}
    for key, name, _ in PAGES:
        with open(os.path.join(ROOT, name), encoding="utf-8") as f:
            bodies[key] = f.read()

    shell = bodies["2"]
    span = find_slides_span(shell)
    if not span:
        raise SystemExit("在 %s 里找不到 slides" % SHELL)

    # 把其它四个页面的 slides 挂到外壳的 page-wrapper 里
    extras = []
    for key, name, _ in PAGES:
        if key == "2":
            continue
        sp = find_slides_span(bodies[key])
        if sp:
            extras.append(bodies[key][sp[0]:sp[1]])
        else:
            print("跳过 %s：没有 slides" % name)

    holder = '<div id="spa-source" style="display:none">' + "\n".join(extras) + '</div>'
    merged = shell[:span[1]] + "\n" + holder + shell[span[1]:]

    # 导航链接改成锚点
    for key, _, _ in PAGES:
        merged = merged.replace('href="%s.html"' % key, 'href="#p-%s"' % key)

    merged = merged.replace("</body>", SWITCHER + "</body>", 1)

    out_path = os.path.join(ROOT, "app.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(merged)
    print("已生成 app.html：%d 字节（合并 %d 个 slides 列表）" %
          (len(merged.encode("utf-8")), 1 + len(extras)))


if __name__ == "__main__":
    main()
