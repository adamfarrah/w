#!/usr/bin/env python3
"""
Build the standalone single-file site.

  1. regenerate i18n/dict.js from i18n/dict.py  (translation source of truth)
  2. re-embed that dictionary into index.html
  3. Base64-inline every image from assets/
  4. write index_standalone.html and Onyx-website.html

Run from the repository root:   python3 build.py
"""
import base64, json, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

# ---------------------------------------------------------------- 1. i18n
sys.path.insert(0, os.path.join(ROOT, 'i18n'))
import dict as D                                    # noqa: E402  (i18n/dict.py)

ar = {k: v[0] for k, v in D.T.items()}
fr = {k: v[1] for k, v in D.T.items()}
dict_js = 'var I18N={ar:%s,fr:%s};' % (
    json.dumps(ar, ensure_ascii=False, separators=(',', ':')),
    json.dumps(fr, ensure_ascii=False, separators=(',', ':')),
)
with open('i18n/dict.js', 'w', encoding='utf-8') as f:
    f.write(dict_js)

s = open('index.html', encoding='utf-8').read()

# swap the embedded dictionary for the freshly generated one
s, n = re.subn(
    r'var I18N=\{.*?\};\n\(function\(\)\{\n  var LANGS',
    lambda m: dict_js + '\n(function(){\n  var LANGS',
    s, count=1, flags=re.S,
)
assert n == 1, 'i18n block not found in index.html'

# ------------------------------------------------------------- 2. images
imgs = {'BG': 'assets/bg_s.jpg', 'PFP': 'assets/pfp_s.png',
        'CLOVER': 'assets/clover_s.png', 'KOI': 'assets/koi_s.jpg'}
mime = {'.jpg': 'image/jpeg', '.png': 'image/png'}
uri = {
    k: 'data:%s;base64,%s' % (
        mime[os.path.splitext(f)[1]],
        base64.b64encode(open(f, 'rb').read()).decode())
    for k, f in imgs.items()
}

s = s.replace('<link rel="preload" as="image" href="assets/pfp.png">\n', '')
s = s.replace('<link rel="icon" id="favi" href="assets/pfp.png">',
              '<link rel="icon" id="favi" href="data:,">')
s = s.replace('<meta property="og:image" content="assets/koi.jpg">', '')
s = s.replace('background:url(assets/bg.jpg) center/cover no-repeat;',
              'background:var(--bgimg) center/cover no-repeat;')
s = s.replace('src="assets/pfp.png"',    'src="data:," data-img="PFP"')
s = s.replace('src="assets/clover.png"', 'src="data:," data-img="CLOVER"')
s = s.replace('src="assets/koi.jpg"',    'src="data:," data-img="KOI"')

# one CSS var + one JS object => each image is embedded exactly once
s = s.replace('  --max:1080px;',
              '  --bgimg:url("%s");\n  --max:1080px;' % uri['BG'], 1)

js = "var IMG={PFP:'%s',CLOVER:'%s',KOI:'%s'};\n" % (
    uri['PFP'], uri['CLOVER'], uri['KOI'])
js += ("document.querySelectorAll('[data-img]')"
       ".forEach(function(n){n.src=IMG[n.getAttribute('data-img')]});\n")
s = s.replace('/* ---------- ICONS ---------- */',
              js + '\n/* ---------- ICONS ---------- */', 1)

# -------------------------------------------------------------- 3. write
assert s.count('assets/') == 0, 'unresolved asset references: %d' % s.count('assets/')

open('index_standalone.html', 'w', encoding='utf-8').write(s)
open('Onyx-website.html', 'w', encoding='utf-8').write(s)

print('translations %d | MB %.2f | external refs %d'
      % (len(D.T), len(s) / 1048576, s.count('assets/')))
