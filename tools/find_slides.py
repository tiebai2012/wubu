import re
s = open("2.html", encoding="utf-8").read()
for m in re.finditer(r'<ul[^>]*class="[^"]*slides[^"]*"[^>]*>', s):
    print("找到:", m.group(0)[:120])
print()
print("所有 ul class:")
for m in re.finditer(r'<ul class="([^"]*)"', s):
    c = m.group(1)
    if "slide" in c or "page" in c:
        print("  ", c[:80])
