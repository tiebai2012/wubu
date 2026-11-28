"""让左上角 logo 可点击，跳转到 www.huojiao.fun。

原站的 logo 只是一个 <img>，外层没有链接（data-image-link 是 javascript:void(0);）。
这里给 logo 的 img 套上一层 <a>，用 CSS 保证不影响布局。
"""
import os, glob, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = "https://www.huojiao.fun"

SCRIPT = """<script>
(function () {
  var url = '%s';
  function boot() {
    // logo 在正常条与吸顶条里各有一份，全部加上链接
    document.querySelectorAll('.s-logo img').forEach(function (img) {
      if (img.closest('a.wubu-logo-link')) return;
      var a = document.createElement('a');
      a.className = 'wubu-logo-link';
      a.href = url;
      a.target = '_blank';
      a.rel = 'noopener';
      a.title = '前往 www.huojiao.fun';
      img.parentNode.insertBefore(a, img);
      a.appendChild(img);
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
</script>
<style id="wubu-logo-css">
  a.wubu-logo-link { display: inline-block; cursor: pointer; }
  a.wubu-logo-link img { display: block; }
</style>
""" % TARGET


def main():
    for path in sorted(glob.glob(os.path.join(ROOT, "*.html"))):
        name = os.path.basename(path)
        with open(path, "rb") as f:
            html = f.read().decode("utf-8")

        html = re.sub(r'<style id="wubu-logo-css">.*?</style>\n?', "", html, flags=re.S)
        html = re.sub(r'<script>\s*\(function \(\) \{\s*var url = .*?前往 www\.huojiao\.fun.*?</script>\n?', "", html, flags=re.S)

        if "s-logo" not in html:
            print("%-12s 没有 logo" % name)
            continue

        html = html.replace("</body>", SCRIPT + "</body>", 1)
        with open(path, "wb") as f:
            f.write(html.encode("utf-8"))
        print("%-12s 已加 logo 链接" % name)


if __name__ == "__main__":
    main()
