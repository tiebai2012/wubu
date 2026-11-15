"""Add the cart / checkout pages, reusing the site chrome from projects.html.

The saved pages keep the platform's own navbar and footer markup; cart.html and
checkout.html are assembled from those same blocks so they look identical.
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTS = os.path.join(ROOT, "projects.html")

DIV_RE = re.compile(r"<div\b|</div\s*>", re.I)
NAV_RE = re.compile(r"""<div[^>]*class=["'][^"']*s-navbar-desktop[^"']*["']""", re.I)
FOOT_RE = re.compile(r"""<div[^>]*class=["'][^"']*s-footer-section[^"']*["']""", re.I)
TITLE_RE = re.compile(r"<title>.*?</title>", re.S | re.I)
DESC_RE = re.compile(r'<meta name="description" content="[^"]*">', re.I)

SHOP_CSS = '<link rel="stylesheet" href="assets/shop/shop.css">\n'
SHOP_JS = '<script src="assets/shop/shop.js" defer></script>\n'


def block_end(html, start):
    """End index of the <div> element that starts at `start`."""
    depth = 0
    pos = start
    while True:
        m = DIV_RE.search(html, pos)
        if not m:
            return len(html)
        depth += -1 if m.group(0).startswith("</") else 1
        pos = m.end()
        if depth == 0:
            return pos


def steps(now):
    return ""


CART_BODY = """
<div class="shop" data-shop-page>
  <h1>购物车</h1>
  <div data-shop-cart></div>
  <p class="shop-note">
    这是演示站点：购物车只保存在本机浏览器，不会提交到任何服务器。
    单价按原站展示的价格区间在规格之间分摊，仅用于演示。
  </p>
</div>
"""

CHECKOUT_BODY = """
<div class="shop" data-shop-page>
  <h1>确认订单</h1>
  <div data-shop-checkout>
    <div class="shop-checkout">
      <form novalidate>
        <fieldset class="shop-fieldset">
          <legend class="shop-subtitle">联系信息</legend>
          <div class="shop-grid2">
            <div class="shop-field">
              <label for="c-name">收货人</label>
              <input id="c-name" name="name" type="text" maxlength="20" autocomplete="name" placeholder="姓名">
              <span class="err" data-err="name"></span>
            </div>
            <div class="shop-field">
              <label for="c-phone">手机号</label>
              <input id="c-phone" name="phone" type="tel" maxlength="11" inputmode="numeric" autocomplete="tel" placeholder="11 位手机号">
              <span class="err" data-err="phone"></span>
            </div>
          </div>
          <div class="shop-field">
            <label for="c-wechat">微信号</label>
            <input id="c-wechat" name="wechat" type="text" maxlength="40" placeholder="格式 [微信号]@wx">
            <span class="err" data-err="wechat"></span>
          </div>
          <div class="shop-field">
            <label for="c-delivery">收货方式</label>
            <select id="c-delivery" name="delivery">
              <option>线下自取（协会指定地点）</option>
              <option>快递到付</option>
            </select>
          </div>
          <div class="shop-field">
            <label for="c-address">收货地址（选择快递时填写）</label>
            <textarea id="c-address" name="address" maxlength="120" placeholder="省 / 市 / 区 / 详细地址"></textarea>
          </div>
          <div class="shop-field">
            <label for="c-memo">备注</label>
            <textarea id="c-memo" name="memo" maxlength="200" placeholder="课时、装帧或其他说明"></textarea>
          </div>
        </fieldset>

        <fieldset class="shop-fieldset">
          <legend class="shop-subtitle">支付方式</legend>
          <div class="shop-pay">
            <label><input type="radio" name="pay" value="微信支付" checked><span class="pay-name">微信支付</span><span class="pay-desc">演示</span></label>
            <label><input type="radio" name="pay" value="支付宝"><span class="pay-name">支付宝</span><span class="pay-desc">演示</span></label>
            <label><input type="radio" name="pay" value="线下支付"><span class="pay-name">线下支付</span><span class="pay-desc">协会面交</span></label>
          </div>
        </fieldset>

        <div class="shop-actions shop-actions--split">
          <a class="shop-btn--link" href="projects.html#buy">返回选购</a>
          <button class="shop-btn shop-btn--wide" type="submit">提交订单</button>
        </div>
      </form>

      <aside class="shop-summary" data-shop-summary></aside>
    </div>

    <div data-shop-done hidden></div>
  </div>

  <p class="shop-note">
    本站没有后台，也没有接支付渠道：提交后只会生成一个假订单号，不会扣款。
    实际购买请按原站说明，线下商议支付方式与交货方式。
  </p>
</div>
"""


def main():
    with open(PROJECTS, "rb") as f:
        html = f.read().decode("utf-8")

    # 1) 购买页挂上购物车脚本
    if "assets/shop/shop.css" not in html:
        html = html.replace("</head>", SHOP_CSS + "</head>", 1)
    if "assets/shop/shop.js" not in html:
        html = html.replace("</body>", SHOP_JS + "</body>", 1)
    with open(PROJECTS, "wb") as f:
        f.write(html.encode("utf-8"))

    # 2) 取站点自己的页头 / 页脚
    navs = list(NAV_RE.finditer(html))
    foot = FOOT_RE.search(html)
    if not navs or not foot:
        raise SystemExit("找不到导航或页脚标记")
    nav_start = navs[0].start()
    foot_start = foot.start()
    # 导航有两份（固定的克隆条 + 常规条），一起保留
    nav_end = max(block_end(html, m.start()) for m in navs if m.start() < foot_start)
    if foot_start < nav_end:
        raise SystemExit("页脚位置异常")
    foot_end = block_end(html, foot_start)

    prefix = html[:nav_start]
    nav_html = html[nav_start:nav_end]
    suffix = html[foot_end:]

    pages = [
        ("checkout.html", "确认订单 - 五不评价协会成员网", "确认订单并选择支付方式（演示，不会真实扣款）。",
         CHECKOUT_BODY),
    ]

    for name, title, desc, body in pages:
        head = TITLE_RE.sub("<title>%s</title>" % title, prefix, count=1)
        head = DESC_RE.sub('<meta name="description" content="%s">' % desc, head, count=1)
        page = head + nav_html + body + html[foot_start:foot_end] + suffix
        with open(os.path.join(ROOT, name), "wb") as f:
            f.write(page.encode("utf-8"))
        print("wrote %-14s %7d bytes" % (name, len(page.encode("utf-8"))))


if __name__ == "__main__":
    main()
