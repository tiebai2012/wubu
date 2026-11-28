p = "tools/merge_pages.py"
s = open(p, encoding="utf-8").read()

# 合并时给每个 slide 打上所属页面的 data-page
s = s.replace('''    combined = shell_slides + "\\n".join(extra)''',
'''    def tag(slides_html, key):
        # 给这段 slides 里的每个 <li class="slide ..."> 标上 data-page
        return re.sub(r'<li class="(slide[^"]*)"',
                      lambda m: '<li class="%s" data-page="%s"' % (m.group(1), key),
                      slides_html)

    combined = tag(shell_slides, "2") + "\\n" + "\\n".join(
        tag(sl, k) for sl, (k, _, _) in zip(extra, [p for p in PAGES if p[0] != "2"])
    )''')
open(p, "w", encoding="utf-8").write(s)
print("ok")
