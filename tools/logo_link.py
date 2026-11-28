"""让左上角 logo 可点击，跳转主站 www.huojiao.fun。

原站 logo 只是 <img>，外层没有链接。这里直接把 <a> 写进 HTML，
不依赖运行时脚本（之前用 JS 生成，部署后可能因脚本没执行而失效）。
"""
import os, glob, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = "https://www.huojiao.fun"

# 匹配 logo 区域的 <img ...>：位于 class="s-logo" 容器内
LOGO_IMG = re.compile(r'(<img\b[^>]*class="crop-default"[^>]*>)', re.I)


def wrap_logo(html):
    """把 .s-logo 里的 img 包进 <a>。"""
    # 找到所有 s-logo 区块，只处理里面的 img
    def do_block(m):
        block = m.group(0)
        if 'wubu-logo-link' in block:
            return block
        # 已经在外层 a 里的不动
        new_block = LOGO_IMG.sub(
            lambda im: '<a class="wubu-logo-link" href="%s" target="_blank" '
                       'rel="noopener" title="\u524d\u5f80 www.huojiao.fun">%s</a>'
                       % (TARGET, im.group(1)),
            block
        )
        return new_block

    # s-logo 到下一个同级大区块之间，简单做法：按 img 所在位置回溯
    out = []
    pos = 0
    for m in re.finditer(r'<div class="s-logo">', html):
        start = m.start()
        # 找这段 s-logo 内的所有 img（到 section 结束）
        end = html.find('</header>', start)
        if end < 0:
            end = html.find('s-nav-items-and-links', start)
        if end < 0:
            continue
        out.append(html[pos:start])
        out.append(do_block(re.match(r'.*', html[start:end], re.S)))
        pos = end
    out.append(html[pos:])
    return "".join(out)


CSS = """<style id="wubu-logo-css">
  a.wubu-logo-link { display: inline-block; cursor: pointer; }
  a.wubu-logo-link img { display: block; }
</style>
"""


def main():
    for path in sorted(glob.glob(os.path.join(ROOT, "*.html"))):
        name = os.path.basename(path)
        with open(path, "rb") as f:
            html = f.read().decode("utf-8")

        # 移除旧的脚本版
        html = re.sub(r'<style id="wubu-logo-css">.*?</style>\n?', "", html, flags=re.S)
        html = re.sub(r"<script>\s*\(function \(\) \{\s*var url = 'https://www\.huojiao\.fun';.*?</script>\n?",
                      "", html, flags=re.S)
        # 移除旧的包裹（可重复执行）
        html = re.sub(r'<a class="wubu-logo-link"[^>]*>(<img\b[^>]*class="crop-default"[^>]*>)</a>',
                      r"\1", html, flags=re.I)

        if 'class="s-logo"' not in html:
            print("%-12s 没有 logo" % name)
            continue

        before = html.count('wubu-logo-link')
        html = wrap_logo(html)
        # logo 上的 data-image-link 是 javascript:void(0);，平台脚本可能据此拦截点击，
        # 已包外层链接后去掉它
        html = re.sub(r'(<a class="wubu-logo-link"[^>]*>\s*<img\b[^>]*?)\s*data-image-link="[^"]*"',
                      r"\1", html, flags=re.I)
        after = html.count('wubu-logo-link')

        html = html.replace("</head>", CSS + "</head>", 1)

        with open(path, "wb") as f:
            f.write(html.encode("utf-8"))
        print("%-12s 静态包了 %d 个 logo 链接（原有 %d）" % (name, after, before))


if __name__ == "__main__":
    main()
