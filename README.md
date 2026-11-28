# 五不评价协会 · 成员网（离线静态版）

从 `wubu-pw.mysxl.cn` 抓下来的五个页面。**推荐用 `app.html`**——一个文件包含全部内容，右上角导航切换不跳转。

## 两个入口

| 文件 | 说明 |
| --- | --- |
| **`app.html`** | 单文件版：五个页面都在这一个文件里，点导航切换（地址栏 `#p-index` / `#p-2` …） |
| `index.html` ~ `5.html` | 分文件版：保留原站的多页形式，点击跳转到对应的 html |

两个入口内容相同，选一个用即可。

## 怎么打开

双击 `app.html` 或 `index.html`。图片、字体都在本地 `assets/` 里（118 个文件，约 13 MB），断网也能看。

部署到 GitHub Pages 时，`CNAME` 已经指向 `wubu.huojiao.fun`，但 GitHub Pages 默认打开的是 `index.html`（分文件版）。想默认打开单文件版，把 `index.html` 换成 `app.html` 的内容即可。

## 相对原站点做的事

页面文字、排版、内容没改，只做了这些：

1. **站内链接改本地**——原站的 `/`、`/2`、`/3` 这些无扩展名路径在本地会 404，已指向对应文件。
2. **资源全部本地化**——原页面用 `//user-assets.sxlcdn.com/...` 这类协议相对地址，`file://` 下会被当磁盘路径、图片全裂；现在都下载到 `assets/` 并改成相对路径。
3. **激活懒加载元素**——原站靠 lazysizes 脚本加 `lazyloaded` 类才应用区块内边距，本地没脚本会纵向错位约 50px，现已直接写进页面。
4. **顶栏白底**——原站白底由脚本滚动时切换，本地补了一条样式固定。
5. **手机端三条杠菜单**——原站移动端左上角的按钮靠平台脚本，现补了等价实现（抽屉式导航）。
6. **桌面端「…」折叠**——复用原站自带的 `.s-nav-ellipsis` 元素；实测阈值 ≥1150 全显示、1050–1149 显示前 4 项、<1050 显示前 3 项。
7. **删掉页脚**——「关于我们 / 资源 / 联系我们」整块移除。
8. **logo 可点击**——本站部署在 `https://wubu.huojiao.fun`，点击左上角 logo 会用**新标签页**打开主站 `https://www.huojiao.fun`，当前页面保留。原站 logo 只是张图，没有链接。
   `<a>` 是**直接写进 HTML 的**，不靠运行时脚本；同时去掉了原 img 上的 `data-image-link="javascript:void(0);"`，避免平台脚本拦掉点击。
9. **手机端只修真实 bug**——成绩页图片格子写死 419px 宽导致整页可横向拖动，仅此一处；其余样式保持原站数值（标题 36px、按钮满宽等）。

## 单文件版是怎么实现的

`tools/merge_pages.py` 以 `2.html` 为外壳，把另外四页的 `<ul class="slides">` 收进一个隐藏容器；
切换导航时把对应那组替换到页面主体里。这样平台的轮播脚本不会把显示状态改回去。

## 目录

```
app.html                                     单文件版（推荐）
index.html  2.html  3.html  4.html  5.html   分文件版
assets/                                      图片、字体、样式、脚本
raw/                                         原始抓取，未做任何改动
screenshots/                                 截图
tools/fetch.py                               抓取页面
tools/make_offline.py                        下载资源、接站内链接
tools/mobile_nav.py                          手机端导航 + 删页脚
tools/nav_ellipsis.py                        桌面端「…」折叠
tools/merge_pages.py                         合并成单文件 app.html
tools/logo_link.py                           给左上角 logo 加外链
```

重新生成：

```powershell
python tools/fetch.py
python tools/make_offline.py
python tools/mobile_nav.py
python tools/nav_ellipsis.py
python tools/merge_pages.py
python tools/logo_link.py
```
