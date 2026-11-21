"""主题样式表里还有 100 多处外链资源（字体分片、图标），逐个下载并本地化。"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import make_offline as mo  # noqa: E402

CSS_DIR = os.path.join(ROOT, "assets")
CSS_URL_RE = mo.CSS_URL_RE
absolute = mo.absolute
download = mo.download

total = ok = failed = 0
for fn in os.listdir(CSS_DIR):
    if not fn.endswith(".css"):
        continue
    path = os.path.join(CSS_DIR, fn)
    with open(path, "rb") as f:
        css = f.read().decode("utf-8", "replace")
    refs = [m.group(2) for m in CSS_URL_RE.finditer(css)
            if m.group(2).startswith(("//", "http")) and not m.group(2).startswith("data:")]
    if not refs:
        continue
    print("%s: %d 个外链资源" % (fn, len(refs)))
    for ref in refs:
        total += 1
        absu = absolute(ref)
        try:
            target = download(absu)
            ok += 1
        except Exception as e:  # noqa: BLE001
            failed += 1
            continue
        rel = os.path.relpath(os.path.join(ROOT, target), os.path.dirname(path)).replace(os.sep, "/")
        for pat in ("url(%s)", "url('%s')", 'url("%s")'):
            css = css.replace(pat % ref, pat % rel)
    with open(path, "wb") as f:
        f.write(css.encode("utf-8"))

print("处理 %d 个，成功 %d，失败 %d" % (total, ok, failed))
print("assets 现有 %d 个文件" % len(os.listdir(CSS_DIR)))
