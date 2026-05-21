# -*- coding: utf-8 -*-
import base64, re, os

def to_b64(path):
    ext = path.split('.')[-1].upper()
    mime = 'image/jpeg' if ext in ['JPG','JPEG'] else 'image/png'
    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    return f'data:{mime};base64,{b64}'

print("Reading invoice_builder.html...")
with open('invoice_builder.html', 'r', encoding='utf-8') as f:
    html = f.read()

# ── Embed main images ──────────────────────────────────────
images = {
    'COMPANY_LOGO_SRC': 'logo.png',
    'SIGNATURE_SRC':    'signature.png',
    'SEAL_SRC':         'company_seal.jpg',
}
for const, fname in images.items():
    try:
        uri = to_b64(fname)
        html = re.sub(
            rf"(const\s+{const}\s*=\s*)['\"][^'\"]*['\"](\s*;[^\n]*)?",
            rf"\1'{uri}';",
            html
        )
        print(f"Embedded {fname}")
    except FileNotFoundError:
        print(f"Skipped {fname} - not found")

# ── Embed footer images ────────────────────────────────────
footer_files = [
    'img_1.png','img_2.png','img_3.png','img_4.png',
    'img_5.png','img_6.png','img_7.png','img_8.png',
]
footer_b64 = []
for i, fname in enumerate(footer_files):
    try:
        uri = to_b64(fname)
        footer_b64.append(f'"{uri}"')
        print(f"Embedded {fname} -> FOOTER_IMAGES[{i}]")
    except FileNotFoundError:
        footer_b64.append('""')
        print(f"Skipped {fname}")

new_array = 'const FOOTER_IMAGES = [\n'
for i, item in enumerate(footer_b64):
    new_array += f'  {item}, // image {i+1}\n'
new_array += '];'

html = re.sub(
    r'const FOOTER_IMAGES\s*=\s*\[[\s\S]*?\]\s*;[^\n]*',
    new_array,
    html
)

# ── Add PWA meta tags ──────────────────────────────────────
pwa_head = '''
    <!-- PWA Support -->
    <link rel="manifest" href="manifest.json">
    <meta name="theme-color" content="#1a3a6b">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="ETS Invoice">
    <meta name="mobile-web-app-capable" content="yes">
'''

pwa_sw = '''
    <script>
    if('serviceWorker' in navigator){
      window.addEventListener('load', function(){
        navigator.serviceWorker.register('sw.js')
          .then(function(reg){ console.log('SW registered'); })
          .catch(function(err){ console.log('SW error:', err); });
      });
    }
    </script>
'''

if 'manifest.json' not in html:
    html = html.replace('</head>', pwa_head + pwa_sw + '\n</head>')

# ── Add working save functions ─────────────────────────────
save_js = '''
/* PWA Save Functions - Works on all devices */
function savePDF(doc, filename){
  try {
    var blob = doc.output('blob');
    var file = new File([blob], filename, {type: 'application/pdf'});
    if(navigator.share && navigator.canShare && navigator.canShare({files: [file]})){
      navigator.share({
        files: [file],
        title: filename,
        text: 'ETS - UGOKINS EMMASON'
      }).catch(function(err){
        downloadBlob(blob, filename);
      });
    } else {
      downloadBlob(blob, filename);
    }
  } catch(e) {
    console.error(e);
    try { doc.save(filename); } catch(e2) { alert('PDF ready: ' + filename); }
  }
}

function saveExcel(wb, filename){
  try {
    var wbout = XLSX.write(wb, {bookType:'xlsx', type:'array'});
    var blob = new Blob([wbout], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    });
    var file = new File([blob], filename, {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    });
    if(navigator.share && navigator.canShare && navigator.canShare({files: [file]})){
      navigator.share({
        files: [file],
        title: filename,
        text: 'ETS - UGOKINS EMMASON Stock Report'
      }).catch(function(err){
        downloadBlob(blob, filename);
      });
    } else {
      downloadBlob(blob, filename);
    }
  } catch(e) {
    console.error(e);
    try { XLSX.writeFile(wb, filename); } catch(e2) { alert('Excel ready: ' + filename); }
  }
}

function downloadBlob(blob, filename){
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();
  setTimeout(function(){
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 1000);
}

function isAndroid(){
  return /android/i.test(navigator.userAgent);
}
'''

# Remove old save functions
for pattern in [
    r'/\* ══ ANDROID FILE SAVE SYSTEM ══ \*/[\s\S]*?(?=\nconst |\nfunction |\nasync function |\n//|\Z)',
    r'/\* ══ ANDROID 13 FILE SAVE SYSTEM ══ \*/[\s\S]*?(?=\nconst |\nfunction |\nasync function |\n//|\Z)',
    r'/\* ══ UNIVERSAL ANDROID FILE SAVE SYSTEM[\s\S]*?(?=\nconst |\nfunction |\nasync function |\n//|\Z)',
    r'/\* ══ SIMPLE UNIVERSAL FILE SAVE[\s\S]*?(?=\nconst |\nfunction |\nasync function |\n//|\Z)',
    r'/\* ══ FINAL SAVE SYSTEM ══ \*/[\s\S]*?(?=\nconst |\nfunction |\nasync function |\n//|\Z)',
    r'/\* PWA Save Functions[\s\S]*?(?=\nconst |\nfunction |\nasync function |\n//|\Z)',
]:
    html = re.sub(pattern, '', html)

# Replace all doc.save and XLSX.writeFile calls
html = re.sub(r"doc\.save\(`([^`]+)`\);", r"savePDF(doc, `\1`);", html)
html = re.sub(r"doc\.save\('([^']+)'\);", r"savePDF(doc, '\1');", html)
html = re.sub(r'XLSX\.writeFile\(wb,\s*`([^`]+)`\);', r"saveExcel(wb, `\1`);", html)
html = re.sub(r"XLSX\.writeFile\(wb,\s*'([^']+)'\);", r"saveExcel(wb, '\1');", html)

# Inject save functions before last </script>
html = html[::-1].replace(
    '>tpircs/<'[::-1],
    (save_js + '\n</script>')[::-1],
    1
)[::-1]

# ── Write final index.html ─────────────────────────────────
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("index.html created!")

# ── Write manifest.json ────────────────────────────────────
manifest = '''{
  "name": "ETS Ugokins Emmason",
  "short_name": "ETS Invoice",
  "description": "Professional Invoice and Business Management Suite",
  "start_url": "./index.html",
  "display": "standalone",
  "background_color": "#eef2f7",
  "theme_color": "#1a3a6b",
  "orientation": "portrait",
  "icons": [
    {"src": "icon.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
    {"src": "icon.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}
  ]
}'''

with open('manifest.json', 'w') as f:
    f.write(manifest)
print("manifest.json created!")

# ── Write sw.js ────────────────────────────────────────────
sw = """const CACHE = 'ets-v1';
const FILES = ['./index.html', './manifest.json'];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(FILES))
  );
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request).catch(() => caches.match('./index.html')))
  );
});
"""

with open('sw.js', 'w') as f:
    f.write(sw)
print("sw.js created!")

# ── Copy logo as icon.png ──────────────────────────────────
try:
    from PIL import Image
    img = Image.open('logo.png').convert('RGB')
    img.save('icon.png')
    print("icon.png created!")
except:
    import shutil
    shutil.copy('logo.png', 'icon.png')
    print("icon.png copied!")

print("")
print("="*50)
print("ALL DONE! Your PWA files are ready:")
print("  - index.html")
print("  - manifest.json")
print("  - sw.js")
print("  - icon.png")
print("="*50)
print("")
print("Upload all 4 files to your GitHub repository:")
print("https://github.com/ugokinsemmason-hub/ets-invoice-app")
print("")
print("Then enable GitHub Pages in Settings -> Pages")
print("Your app will be live at:")
print("https://ugokinsemmason-hub.github.io/ets-invoice-app")