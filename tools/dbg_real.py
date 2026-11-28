import re
s = open("index.html", encoding="utf-8").read()
# 找 s-logo 区块，看 img 外层是否真有 a
i = s.find('class="s-logo"')
seg = s[i:i+2500]
print("=== s-logo 区块 ===")
for m in re.finditer(r"<(a|img)\b[^>]*>", seg):
    tag = m.group(0)
    print("  ", tag[:200])
