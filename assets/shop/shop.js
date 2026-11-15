/* 五不评价协会 · 购物车 / 结算
   纯前端演示：数据只存在浏览器 localStorage，不发送任何请求。
   购物车按原站的样式做成页内弹层：有商品时是满屏高的白色面板，
   空车时是居中的小对话框。 */
(function () {
  "use strict";

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var KEY = "wubu.shop.cart";

  /* 规格单价（元）。取自原站商品接口：
     GET /r/v1/sites/12725085/products —— variations[].price（单位：分） */
  var PRICES = {
    "八课时": 2.5, "十二课时": 3, "十六课时": 3.5, "二十课时": 4, "二十四课时": 4.5,
    "整册": 5, "单页": 1, "整本胶带加固": 10
  };

  /* ---------- 存取 ---------- */
  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch (e) { return []; }
  }
  function save(items) {
    try { localStorage.setItem(KEY, JSON.stringify(items)); } catch (e) { /* 隐私模式 */ }
  }
  function count(items) {
    return (items || load()).reduce(function (n, it) { return n + it.qty; }, 0);
  }
  function total(items) {
    return (items || load()).reduce(function (s, it) { return s + it.price * it.qty; }, 0);
  }
  function money(n) {
    return "¥" + (Math.round(n * 100) / 100).toFixed(2);
  }
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  /* ---------- 提示 ---------- */
  var toastEl = null, toastTimer = null;
  function toast(msg) {
    if (!toastEl) {
      toastEl = document.createElement("div");
      toastEl.className = "shop-toast";
      toastEl.setAttribute("role", "status");
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = msg;
    void toastEl.offsetWidth;
    toastEl.classList.add("is-open");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove("is-open"); }, 2300);
  }

  /* ---------- 导航栏购物车 ---------- */
  function paintNav() {
    var n = count();
    $$(".item-number").forEach(function (el) { el.textContent = String(n); });
    $$(".s-shipping-cart-item").forEach(function (item) {
      item.title = n ? "购物车里有 " + n + " 件商品" : "您的购物车还是空的，赶快去挑选商品吧！";
    });
  }
  function bindNav() {
    paintNav();
    // 用事件委托：滚动后克隆出来的吸顶条里的购物车图标也能点
    if (!document.documentElement.dataset.cartDelegated) {
      document.documentElement.dataset.cartDelegated = "1";
      document.addEventListener("click", function (e) {
        var item = e.target.closest(".s-shipping-cart-item");
        if (!item) return;
        e.preventDefault();
        openCart();
      });
    }
    $$(".s-shipping-cart-item").forEach(function (item) {
      item.style.cursor = "pointer";
    });
  }

  /* ---------- 购物车弹层（结构与样式取自原站） ---------- */
  var modal = null;

  /* 原站购物车面板的骨架，class 全部照抄渲染结果 */
  var ITEM_TPL =
    '<div class="cart-item-wrapper"><div class="product-info">' +
      '<div class="image"></div>' +
      '<div class="info-content">' +
        '<div class="detail">' +
          '<div class="name"></div>' +
          '<div class="specification-item"><div class="variation-name"></div></div>' +
        '</div>' +
        '<div class="quantity-price-group">' +
          '<div class="quantity-panel"><div class="operation-item">' +
            '<div class="delete-icon">\u00d7</div>' +
            '<input type="text" maxlength="5" class="quantity-input" value="1">' +
            '<div class="plus-icon">+</div>' +
          '</div></div>' +
          '<div class="product-price"></div>' +
        '</div>' +
      '</div>' +
    '</div></div>';

  var PANEL_TPL =
    '<div class="buyer-checkout-dialog-wrapper">' +
      '<div role="dialog" aria-modal="true" class="s-kit-modal buyer-checkout-dialog css-gp2qxq">' +
        '<div tabindex="0" style="outline:none">' +
          '<div class="s-kit-modal-content"><div class="s-kit-modal-body">' +
            '<div class="close-modal-icon"></div>' +
            '<div class="shopping-cart-wrapper"><div class="shopping-container">' +
              '<div id="cart-title" class="cart-title">购物车</div>' +
              '<div class="cart-panel"></div>' +
              '<div id="cart-footer" class="shopping-footer">' +
                '<div class="price-panel"><div class="price-info">' +
                  '<span class="label">小计</span>' +
                  '<div class="amount-group">' +
                    '<div class="s-kit-currency-tag currency">CNY</div>' +
                    '<span class="amount">\u00a50.00</span>' +
                  '</div>' +
                '</div></div>' +
                '<div class="checkout-buttons">' +
                  '<div class="s-button-package button-fill-solid full-width-on-mobile css-1o1c9ah css-1eq0yei0">' +
                    '<div class="s-common-button checkout-btn"><i class="s-kit-icon"></i>\u4e0b\u5355\u7ed3\u7b97</div>' +
                  '</div>' +
                '</div>' +
              '</div>' +
            '</div></div>' +
          '</div>' +
        '</div>' +
      '</div>' +
    '</div>';

  function ensureModal() {
    if (modal) return modal;
    modal = document.createElement("div");
    modal.className = "cart-modal";
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");
    modal.setAttribute("aria-label", "\u8d2d\u7269\u8f66");
    modal.innerHTML = PANEL_TPL;
    document.body.appendChild(modal);
    bindModalEvents();
    return modal;
  }

  var cartIndex = -1;

  function bindModalEvents() {
    modal.addEventListener("click", function (e) {
      if (e.target === modal) return closeCart();
      if (e.target.closest(".close-modal-icon")) return closeCart();
      if (e.target.closest(".checkout-btn")) {
        window.location.href = "checkout.html";
        return;
      }
      var item = e.target.closest(".cart-item-wrapper");
      if (!item) return;
      var i = Number(item.getAttribute("data-i"));
      var items = load();
      if (e.target.closest(".delete-icon")) {
        items.splice(i, 1);
      } else if (e.target.closest(".plus-icon")) {
        items[i].qty = Math.min(99, items[i].qty + 1);
      } else {
        return;
      }
      save(items);
      paintNav();
      renderCart();
    });

    modal.addEventListener("input", function (e) {
      if (!e.target.classList.contains("quantity-input")) return;
      var item = e.target.closest(".cart-item-wrapper");
      var i = Number(item.getAttribute("data-i"));
      var items = load();
      items[i].qty = Math.max(1, Math.min(99, parseInt(e.target.value, 10) || 1));
      save(items);
      var priceEl = item.querySelector(".product-price");
      if (priceEl) priceEl.textContent = money(items[i].price * items[i].qty);
      var sum = modal.querySelector(".shopping-footer .amount");
      if (sum) sum.textContent = money(total(items));
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && modal.classList.contains("is-open")) closeCart();
    });
  }

  function renderCart() {
    ensureModal();
    var items = load();
    var panel = modal.querySelector(".cart-panel");
    var foot = modal.querySelector(".shopping-footer");
    var title = modal.querySelector(".cart-title");

    if (!items.length) {
      panel.innerHTML =
        '<div style="padding:0 40px 40px"><div class="empty-cart-container">' +
        '<div class="label">\u4f60\u7684\u8d2d\u7269\u8f66\u4e3a\u7a7a</div>' +
        '<div class="s-button-package button-fill-solid full-width-on-mobile css-1o1c9ah css-1eq0yei0">' +
        '<div class="s-common-button continue-btn">\u7ee7\u7eed\u8d2d\u7269</div></div></div></div>';
      foot.style.display = "none";
      title.textContent = "\u8d2d\u7269\u8f66";
      panel.querySelector(".continue-btn").addEventListener("click", closeCart);
      return;
    }

    foot.style.display = "";
    title.textContent = "\u8d2d\u7269\u8f66";
    panel.innerHTML = "";
    items.forEach(function (it, i) {
      var wrap = document.createElement("div");
      wrap.innerHTML = ITEM_TPL;
      var node = wrap.firstChild;
      node.setAttribute("data-i", String(i));
      var img = node.querySelector(".image");
      if (it.img) img.style.backgroundImage = 'url("' + it.img + '")';
      node.querySelector(".name").textContent = it.name;
      node.querySelector(".variation-name").textContent = it.variant;
      node.querySelector(".quantity-input").value = String(it.qty);
      node.querySelector(".product-price").textContent = money(it.price * it.qty);
      panel.appendChild(node);
    });
    var sum = modal.querySelector(".shopping-footer .amount");
    if (sum) sum.textContent = money(total(items));
  }

  function openCart() {
    renderCart();
    modal.classList.add("is-open");
    document.body.style.overflow = "hidden";
  }
  function closeCart() {
    if (!modal) return;
    modal.classList.remove("is-open");
    document.body.style.overflow = "";
  }

  /* ---------- 商品 → 购物车 ---------- */
  function priceRange(text) {
    var nums = (text || "").match(/\d+(?:\.\d+)?/g);
    if (!nums) return [0, 0];
    var list = nums.map(Number);
    return [Math.min.apply(null, list), Math.max.apply(null, list)];
  }

  function readProduct(row) {
    var nameEl = $(".s-ecommerce-row-view-product-name", row);
    var codeEl = $(".s-ecommerce-row-view-product-desc", row);
    var priceEl = $(".s-ecommerce-row-view-product-pricing", row);
    var select = $(".s-ecommerce-row-view-product-select select", row);
    var qtyInput = $(".s-ecommerce-row-view-product-quantity input", row) || $('input[type="number"]', row);
    var img = $(".s-ecommerce-row-view-product-image-wrapper img", row) || $("img", row);

    var options = select ? $$("option", select).filter(function (o) {
      return !o.disabled && o.value !== "" && o.textContent.trim() !== "选择";
    }) : [];
    var variant = "";
    var price = 0;
    var range = priceRange(priceEl ? priceEl.textContent : "");

    if (options.length) {
      var idx = options.findIndex(function (o) { return o.selected; });
      if (idx < 0) idx = 0;
      variant = options[idx].textContent.trim();
      price = Object.prototype.hasOwnProperty.call(PRICES, variant)
        ? PRICES[variant]
        : (options.length === 1 ? range[0]
           : range[0] + (range[1] - range[0]) * (idx / (options.length - 1)));
    } else {
      price = range[0];
    }

    return {
      id: ((nameEl ? nameEl.textContent : "") + "|" + variant).trim(),
      name: nameEl ? nameEl.textContent.trim() : "评价手册",
      code: codeEl ? codeEl.textContent.trim() : "",
      variant: variant || "标准版",
      price: Math.round(price * 100) / 100,
      qty: Math.max(1, parseInt(qtyInput ? qtyInput.value : "1", 10) || 1),
      img: img ? (img.currentSrc || img.src || img.getAttribute("data-src") || "") : ""
    };
  }

  function addToCart(product) {
    var items = load();
    var hit = items.filter(function (it) { return it.id === product.id; })[0];
    if (hit) { hit.qty += product.qty; } else { items.push(product); }
    save(items);
    paintNav();
    toast("已加入购物车：" + product.variant + " ×" + product.qty);
  }

  function bindProducts() {
    var buttons = $$(".s-ecommerce-row-view-product-order-btn");
    if (!buttons.length) return;
    buttons.forEach(function (btn) {
      if (btn.dataset.shopBound) return;
      btn.dataset.shopBound = "1";
      btn.style.cursor = "pointer";
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        var row = btn.closest(".s-ecommerce-row-view-product");
        if (row) addToCart(readProduct(row));
      });
    });
  }

  /* ---------- 结算页 ---------- */
  function renderSummary(box) {
    var items = load();
    if (!items.length) return false;
    box.innerHTML = "<h2>订单摘要</h2>" +
      items.map(function (it) {
        return '<div class="line"><span>' + esc(it.name) + "<br><em>" + esc(it.variant) + " ×" + it.qty +
          "</em></span><span>" + money(it.price * it.qty) + "</span></div>";
      }).join("") +
      '<div class="line"><span>运费</span><span>免运费</span></div>' +
      '<div class="sum"><span>应付</span><strong>' + money(total(items)) + "</strong></div>";
    return true;
  }

  function initCheckoutPage() {
    var root = $("[data-shop-checkout]");
    if (!root) return;
    var summary = $("[data-shop-summary]", root);

    if (!renderSummary(summary) || !load().length) {
      root.innerHTML =
        '<div class="shop-empty"><p>购物车是空的，先挑两本手册吧。</p>' +
        '<a class="shop-btn" href="projects.html#buy">去选购</a></div>';
      return;
    }

    var form = $("form", root);
    var done = $("[data-shop-done]", root);

    function setErr(name, msg) {
      var el = $('[data-err="' + name + '"]', form);
      if (el) el.textContent = msg || "";
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var name = form.elements.name.value.trim();
      var phone = form.elements.phone.value.trim();
      var wechat = form.elements.wechat.value.trim();
      var ok = true;

      setErr("name", ""); setErr("phone", ""); setErr("wechat", "");
      if (name.length < 2) { setErr("name", "请填写收货人姓名"); ok = false; }
      if (!/^1[3-9]\d{9}$/.test(phone)) { setErr("phone", "请填写 11 位手机号"); ok = false; }
      if (!wechat) { setErr("wechat", "请填写微信号，格式 [微信号]@wx"); ok = false; }
      if (!ok) {
        var first = $(".err:not(:empty)", form);
        if (first) first.closest(".shop-field").querySelector("input").focus();
        return;
      }

      var amount = total();
      var no = "WUBU" + Date.now().toString().slice(-10);
      var pay = (form.elements.pay && form.elements.pay.value) || "微信支付";
      save([]);

      form.hidden = true;
      root.querySelector(".shop-checkout").hidden = true;
      done.hidden = false;
      done.innerHTML =
        '<div class="shop-done"><div class="tick">✓</div>' +
        '<div class="no">订单号 ' + no + " · " + pay + "</div>" +
        '<div class="amount">' + money(amount) + "</div>" +
        '<p class="tip">这是演示站点，没有后台，也没有真正扣款。<br>' +
        "实际购买请联系协会，按官网说明线下商议支付方式与交货方式。</p>" +
        '<a class="shop-btn" href="index.html">返回首页</a></div>';
      var title = $(".shop h1");
      if (title) title.textContent = "订单已提交";
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  /* ---------- 启动 ---------- */
  function init() {
    bindNav();
    bindProducts();
    initCheckoutPage();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
