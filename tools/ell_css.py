# 抓原站省略号的样式
import re
css = open("assets/main_v4.38f9eca0649dd23d2709.bundle.css", encoding="utf-8", errors="replace").read()
for key in ("ellipsis-icon", "s-nav-ellipsis", "s-nav-dropdown-text", "drop-down-icon-bold"):
    ms = re.findall(r"[^{}]{0,60}"+re.escape(key)+r"[^{}]*\{[^}]{0,180}\}", css)
    print("==", key, len(ms))
    for m in ms[:4]:
        print("   ", m.strip()[:190])
