"""删除每页底部的页脚块（关于我们 / 资源 / 联系我们）。

页脚是平台渲染的一整块 <div class="... s-footer-section ...">，按标签平衡整块移除，
顺手把外面那层 #s-footer-section-container 也去掉（如果它已经空了）。
"""
import os, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIV_RE = re.compile(r"<div\b|</div\s*>", re.I)
FOOT_RE = re.compile(r"""<div[^>]*class=["'][^"']*s-footer-section[^"']*["']""", re.I)
CONTAINER_RE = re.compile(r"""<div[^>]*id=["']s-footer-section-container["'][^>]*>\s*</div>""", re.I)


def block_end(html, start):
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


def main():
    for path in sorted(glob.glob(os.path.join(ROOT, "*.html"))):
        with open(path, "rb") as f:
            html = f.read().decode("utf-8")
        m = FOOT_RE.search(html)
        if not m:
            print("%-18s 没有页脚" % os.path.basename(path))
            continue
        end = block_end(html, m.start())
        new = html[:m.start()] + html[end:]
        new = CONTAINER_RE.sub("", new)
        with open(path, "wb") as f:
            f.write(new.encode("utf-8"))
        print("%-18s 删除 %6d 字节" % (os.path.basename(path), len(html) - len(new)))


if __name__ == "__main__":
    main()
