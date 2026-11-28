p = "tools/merge_pages.py"
s = open(p, encoding="utf-8").read()

old_start = s.find('    switcher = """')
old_end = s.find('"""\n    out = out.replace("</body>"', old_start)
new = '''    switcher = """
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
'''
s = s[:old_start] + new + s[old_end:]
open(p, "w", encoding="utf-8").write(s)
print("ok")
