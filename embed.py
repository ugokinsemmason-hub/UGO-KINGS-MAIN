import base64, re

# ── MAIN IMAGES (logo, signature, seal) ──────────────────
main_files = {
    "COMPANY_LOGO_SRC": "logo.png",        # ← rename to your actual logo filename
    "SIGNATURE_SRC":    "signature.png",
    "SEAL_SRC":         "company_seal.jpg",
}

# ── FOOTER IMAGES (8 slots) ──────────────────────────────
# Add your 8 footer image filenames here in order
footer_files = [
    "img_1.png",   # image 1
    "img_2.png",   # image 2
    "img_3.png",   # image 3
    "img_4.png",   # image 4
    "img_5.png",   # image 5
    "img_6.png",   # image 6
    "img_7.png",   # image 7
    "img_8.png",   # image 8
]

# ─────────────────────────────────────────────────────────

def to_base64(filename):
    ext = filename.split(".")[-1].upper()
    mime = "image/jpeg" if ext in ["JPG", "JPEG"] else "image/png"
    with open(filename, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{b64}"

with open("ets_invoice.html", "r", encoding="utf-8") as f:
    html = f.read()

# ── Embed main images ────────────────────────────────────
for const, filename in main_files.items():
    try:
        data_uri = to_base64(filename)
        html = re.sub(
            rf'(const {const}\s*=\s*)"[^"]*"',
            rf'\1"{data_uri}"',
            html
        )
        print(f"✅ Embedded {filename} → {const}")
    except FileNotFoundError:
        print(f"⚠️  Skipped {filename} (file not found)")

# ── Embed footer images into array ───────────────────────
footer_b64_list = []
for i, filename in enumerate(footer_files):
    try:
        data_uri = to_base64(filename)
        footer_b64_list.append(f'"{data_uri}"')
        print(f"✅ Embedded {filename} → FOOTER_IMAGES[{i}]")
    except FileNotFoundError:
        footer_b64_list.append('""')
        print(f"⚠️  Skipped {filename} (file not found) → FOOTER_IMAGES[{i}] left empty")

# Build the new array string
new_array = "const FOOTER_IMAGES = [\n"
for i, item in enumerate(footer_b64_list):
    new_array += f"  {item}, // image {i+1}\n"
new_array += "];"

# Replace the old FOOTER_IMAGES array in the HTML
html = re.sub(
    r'const FOOTER_IMAGES\s*=\s*\[[\s\S]*?\];',
    new_array,
    html
)

with open("ets_invoice.html", "w", encoding="utf-8") as f:
    f.write(html)

print("\n✅ Done! Open ets_invoice.html in Chrome or Edge.")
