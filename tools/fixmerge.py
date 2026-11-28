p = "tools/merge_pages.py"
s = open(p, encoding="utf-8").read()
s = s.replace('''    m = re.search(r'<ul class="slides[^"]*"[^>]*>', html)''',
'''    m = re.search(r'<ul\\b[^>]*class="[^"]*\\bslides\\b[^"]*"[^>]*>', html)''')
# 修 escape warning
s = s.replace('var m = /#p-(\\d+)/.exec(location.hash);', 'var m = /#p-([0-9]+)/.exec(location.hash);')
open(p, "w", encoding="utf-8").write(s)
print("ok")
