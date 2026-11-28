import re
s = open("app.html", encoding="utf-8").read()
print("slides 数量:", s.count('<ul class="slides'))
print("slide 数量:", len(re.findall(r'<li class="slide', s)))
print("锚点链接:", len(re.findall(r'href="#p-\d"', s)))
# 每个页面主体是否都在
for n in range(1,6):
    print("  #p-%d 出现: %s" % (n, ('href="#p-%d"' % n) in s))
