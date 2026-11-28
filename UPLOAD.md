# 上传清单

把下面这些推到 GitHub Pages 仓库的根目录（和 `CNAME` 同级），线上就是最新版。

## 必传

```
index.html
2.html
3.html
4.html
5.html
app.html        （可选，单文件版）
CNAME           （已存在，内容 wubu.huojiao.fun，别覆盖掉）
assets/         ← 整个目录，118 个文件，约 13 MB，漏了图片会裂
```

## 说明

- **`index.html` 是首页**。GitHub Pages 打开域名时默认读它，所以首页必须是这个名字。
- 想用单文件版：把 `app.html` 内容复制进 `index.html` 上传，或者直接访问 `/app.html`。
- `raw/`、`screenshots/`、`tools/`、`README.md` 是本地资料，**不用上传**。

## 上传后自查

打开 `https://wubu.huojiao.fun/` ，确认这几点：

1. **左上角 logo 有链接**——鼠标移上去变手型，点一下会新开标签页到 `www.huojiao.fun`
2. 页面底部**没有**「关于我们 / 资源 / 联系我们」页脚
3. 手机宽度下左上角有三条杠菜单
4. 窗口拉窄到 1150 以下，右上角菜单末尾变成 `…`

## 如果 logo 还是点不动

在浏览器里按 F12 → Console，执行：

```js
document.querySelectorAll('a.wubu-logo-link').length
```

- 返回 `0` → 线上还是旧文件，没上传成功
- 返回 `6` 左右 → 文件是对的，问题在点击被拦，把结果告诉我
