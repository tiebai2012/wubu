"""手机端导航：完全按原站的形态还原。

原站手机端（实测 390px）：
  - 左上角三条杠按钮，整个顶栏是一条 fixed 高度 60px 的横条
  - 中间是 logo
  - 右边是购物车图标（带红色角标）—— 按用户要求不做购物车，这里留空
  - 点三条杠展开抽屉式导航
"""

MGAP = 8  # 与 s-font-body 的间距一致

MOBILE_CSS = """/* 手机端导航（还原原站形态：60px 高顶栏 + 左上三条杠 + 居中 logo） */
.m-nav-toggle {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  width: 60px;
  height: 60px;
  border: 0;
  background: transparent;
  cursor: pointer;
  padding: 0;
  z-index: 1200;
}
.m-nav-toggle span {
  display: block;
  width: 22px;
  height: 2px;
  margin: 4px 0 4px 17px;
  background: #000;
  border-radius: 0;
  transition: transform .25s, opacity .25s;
}
.m-nav-toggle.is-open span:nth-child(1) { transform: translateY(6px) rotate(45deg); }
.m-nav-toggle.is-open span:nth-child(2) { opacity: 0; }
.m-nav-toggle.is-open span:nth-child(3) { transform: translateY(-6px) rotate(-45deg); }

.m-nav-drawer {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 78%;
  max-width: 320px;
  background: #fff;
  z-index: 1199;
  box-shadow: 2px 0 16px rgba(0, 0, 0, .12);
  transform: translateX(-100%);
  transition: transform .28s ease;
  overflow-y: auto;
  padding: 68px 0 24px;
}
.m-nav-drawer.is-open { transform: translateX(0); }
.m-nav-drawer ul { list-style: none; margin: 0; padding: 0; }
.m-nav-drawer li { border-bottom: 1px solid rgba(0, 0, 0, .06); }
.m-nav-drawer a {
  display: block;
  padding: 16px 24px;
  font-size: 17px;
  line-height: 1.4;
  color: #222;
  text-decoration: none;
}
.m-nav-drawer a.is-active { font-weight: 700; color: #000; }

.m-nav-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, .35);
  z-index: 1198;
  opacity: 0;
  pointer-events: none;
  transition: opacity .28s;
}
.m-nav-mask.is-open { opacity: 1; pointer-events: auto; }

body.m-nav-locked { overflow: hidden; }

@media (max-width: 767px) {
  .m-nav-toggle { display: block; }
}
"""

MOBILE_JS = """<script>
  (function () {
    var btn = document.getElementById('m-nav-toggle');
    var drawer = document.getElementById('m-nav-drawer');
    var mask = document.getElementById('m-nav-mask');
    if (!btn || !drawer) return;
    function set(open) {
      btn.classList.toggle('is-open', open);
      drawer.classList.toggle('is-open', open);
      mask.classList.toggle('is-open', open);
      document.body.classList.toggle('m-nav-locked', open);
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    }
    btn.addEventListener('click', function () {
      set(!drawer.classList.contains('is-open'));
    });
    mask.addEventListener('click', function () { set(false); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') set(false);
    });
    drawer.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') set(false);
    });
  })();
</script>
"""
