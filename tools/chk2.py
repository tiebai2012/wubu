import re
s = open("app.html", encoding="utf-8").read()
print("总 slide:", len(re.findall(r'<li class="slide', s)))
print("带 data-page:", len(re.findall(r'data-page="', s)))
for k in ("index","2","3","4","5"):
    print("  %s: %d 个" % (k, s.count('data-page="%s"' % k)))
