# 五不评价协会 · 成员网（静态存档）

从 `wubu-pw.mysxl.cn` 逐页保存的静态页面，共五个。

| 文件 | 原站路径 | 内容 |
| --- | --- | --- |
| `index.html` | `/` | 首页：恪守五不，讲好道法 / 核心价值观 |
| `projects.html` | `/2` | 选择项目 / 购买评价手册 |
| `standards.html` | `/3` | 下载标准 |
| `results.html` | `/4` | 历史评价成绩 |
| `about.html` | `/5` | 关于五不 / 五不条例 |

直接双击打开即可。样式、图片、字体仍指向原站 CDN，**需要联网**。

## 对原站的改动

1. **顶栏重写。** 平台那套导航是两条克隆条 + 一堆条件类，切换页面时状态不一致（这就是"点右上角换页面就出问题"的原因）。现在整块换成自己写的 `header.wubu-bar`：
   - 固定定位、白底、高 100、内容区 1240 居中（左右各 32.5 内边距）
   - 位置按原站实测坐标：logo 127.7×60 @ (125,20)、站名 20px @ (268.7,37)、菜单 16px/700、回到顶部按钮 100×40 @ (1200,30)
   - 滚动超过 60px 时加原站那条 `0 1px rgba(0,0,0,.12)` 投影
   - 当前页在导航里加深并加下划线
2. **去掉平台脚本**——原站单页应用会按 URL 路径重渲染，本地打开会被改写。
3. **删掉每页底部页脚**（关于我们 / 资源 / 联系我们）。
4. **导航高亮**：每个页面高亮自己那一项（`is-active`）。
5. 站内链接改本地文件、`//` 补成 `https://`、字体样式表改成立即生效、站内链接不新开标签页。
6. **统一滚动条**：`html { overflow-y: scroll }`，五页顶栏宽度一致（1425）。
7. 顶栏购物车图标保留，**点了没有反应**（没有购物车逻辑）。

## 已知

- 手机上汉堡菜单靠脚本，静态版窄屏只显示标题。
- 「加入购物车 / 下单结算 / 购买」都不会有反应——按你的要求，只留图标，不做那套。

## 目录

```
index.html  projects.html  standards.html  results.html  about.html   五个页面
raw/                                                                  原始抓取（含商品接口数据）
screenshots/                                                          页面截图
tools/fetch.py                                                        抓取页面
tools/save_pages.py                                                   生成五个页面
tools/strip_footer.py                                                 删除页脚
tools/rebuild_nav.py                                                  重写顶部栏（五页统一）
tools/crawl_site.py                                                   整站爬取（9 个页面清单）
tools/capture.js                                                      截图/状态取证脚本（CDP）
```

重新生成：

```powershell
python tools/fetch.py
python tools/save_pages.py
python tools/strip_footer.py
python tools/rebuild_nav.py
```
