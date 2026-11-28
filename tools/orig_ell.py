import re
s = open("raw/projects.html", encoding="utf-8").read()
i = s.find("s-nav-ellipsis")
seg = s[i-100:i+3000]
print("=== 原站省略号元素结构 ===")
print(seg[:2500].replace("><", ">\n<"))
