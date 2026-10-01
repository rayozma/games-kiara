import os, re, sys, json, time, getpass, urllib.request, urllib.error
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
VOICE_ID = "JaUVfDrFcfwGIsv8X2kN"
MODEL = "eleven_turbo_v2_5"  # supports language_code; multilingual_v2 guesses the language and mispronounces short words
LANG = "id"
OUT = "audio"
LETTER_SAY = {"A":"a","B":"be","C":"ce","D":"de","E":"e","F":"ef","G":"ge","H":"ha","I":"i","J":"je","K":"ka","L":"el","M":"em","N":"en","O":"o","P":"pe","Q":"ki","R":"er","S":"es","T":"te","U":"u","V":"fe","W":"we","X":"eks","Y":"ye","Z":"zet"}
HURUF = [("A","Apel"),("B","Bola"),("C","Cacing"),("D","Dokter"),("E","Elang"),("F","Film"),("G","Gajah"),("H","Harimau"),("I","Ikan"),("J","Jerapah"),("K","Kucing"),("L","Lebah"),("M","Monyet"),("N","Naga"),("O","Ombak"),("P","Pisang"),("Q","Quran"),("R","Rusa"),("S","Singa"),("T","Topi"),("U","Ular"),("V","Vitamin"),("W","Wortel"),("X","Xilofon"),("Y","Yoyo"),("Z","Zebra")]
ANGKA = ["Satu","Dua","Tiga","Empat","Lima","Enam","Tujuh","Delapan","Sembilan","Sepuluh","Sebelas","Dua Belas","Tiga Belas","Empat Belas","Lima Belas","Enam Belas","Tujuh Belas","Delapan Belas","Sembilan Belas","Dua Puluh"]
HEWAN = ["Kucing","Anjing","Sapi","Ayam","Bebek","Kuda","Kambing","Gajah","Singa","Harimau","Jerapah","Monyet","Kelinci","Ikan","Burung","Ular","Buaya","Panda","Zebra","Kupu-kupu"]
COLORS = ["merah","biru","kuning","hijau","ungu","merah muda"]
NAMES = ["gaun","sepatu","mahkota","tas","kalung","topi","kacamata","payung","sepatu bot","jas hujan","syal","jaket"]
WEATHER = {"hujan":("Hari ini hujan!","supaya tidak basah",["payung","jas hujan","sepatu bot"]),"panas":("Hari ini panas sekali!","supaya tidak kepanasan",["topi","kacamata"]),"dingin":("Hari ini dingin!","supaya tetap hangat",["syal","jaket"])}
WHY = {"kacamata":"supaya mata tidak silau"}
TOPS = ["tanpa lengan","lengan pendek","lengan panjang","lengan balon"]
SKIRTS = ["panjang","mengembang","lipit","pendek"]
TOGGLES = ["kalung","topi","kacamata","payung","syal","jaket","jas hujan","sepatu bot"]
# Spoken-text overrides for lines the voice mispronounces (display text -> what is sent to ElevenLabs)
SAY = {
    'A. Apel': "a. Ap'l.",
    'C. Cacing': 'cé. Cacing.',
    'F. Film': 'F. Film.',
    'T. Topi': 'té. Topi.',
    'Cari huruf A': 'Cari huruf A.',
    'Cari huruf C': 'Cari huruf cé.',
    'Cari huruf D': 'Cari huruf dé.',
    'Cari huruf G': 'Cari huruf gé.',
    'Cari huruf J': 'Cari huruf jé.',
    'Cari huruf O': 'Cari huruf O.',
    'Cari huruf S': 'Cari huruf... es.',
    'Cari huruf T': 'Cari huruf té.',
    'Cari huruf V': 'Cari huruf vé.',
    'Cari huruf W': 'Cari huruf we.',
    'Cari huruf Y': 'Cari huruf yé.',
    'Lima Belas': "Lima b'las.",
    'Delapan Belas': 'Delapan blas.',
    'Cari angka 15': 'Cari angka lima blas.',
    'Cari angka 18': 'Cari angka delapan blas.',
    'Cari angka 11': 'Cari angka sebelas.',
    'Jerapah': 'Jerapah.',
}
# Candidate spellings to compare with --preview (writes audio_preview/index.html); winners go into SAY
# Unspoken text sent before/after a line to steer pronunciation (display text -> (previous_text, next_text))
CONTEXT = {"E. Elang": ("Ini burung elang.", "Elang terbang tinggi.")}
PREVIEW = {}
TEST = ["A. Apel","Cari huruf B","Cari huruf W","Cari angka 7","Dua Belas","Cari Kucing","Pintar! Pakai payung supaya tidak basah."]

def slug(t): return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")

def phrases():
    p = []
    for l, w in HURUF: p += [(f"{l}. {w}", f"{LETTER_SAY[l]}. {w}"), (f"Cari huruf {l}", f"Cari huruf {LETTER_SAY[l]}")]
    for i, w in enumerate(ANGKA, 1): p += [(w, w), (f"Cari angka {i}", f"Cari angka {w.lower()}")]
    for h in HEWAN: p += [(h, h), (f"Cari {h}", f"Cari {h}")]
    for c in COLORS:
        for t in ["sepatu","tas","mahkota"]: p += [(f"Gaun Princess warna {c}. Cari {t} warna {c}!",)*2, (f"Pintar! {t.capitalize()} {c}, sama dengan gaunnya!",)*2]
    for say, why, items in WEATHER.values():
        p.append((f"{say} Princess pakai apa ya?",)*2)
        for it in items: p.append((f"Pintar! Pakai {it} {WHY.get(it, why)}.",)*2)
    for n in NAMES: p += [(f"Cari {n}!",)*2, (f"Pintar! Ini {n}.",)*2]
    for lab in ["Gaun","Rok","Sepatu","Mahkota","Tas"]: p += [(f"{lab} {c}",)*2 for c in COLORS]
    p += [(f"baju {k}",)*2 for k in TOPS] + [(f"rok {k}",)*2 for k in SKIRTS] + [(t, t) for t in TOGGLES] + [("Ayo dandani Princess!",)*2, ("Wah, Princess cantik sekali!",)*2]
    seen, out = set(), []
    for d, s in p:
        if slug(d) not in seen: seen.add(slug(d)); out.append((d, SAY.get(d, s)))
    return out

def tts(key, text, model=MODEL, stability=0.55, context=(None, None)):
    req = {"text": text, "model_id": model, "voice_settings": {"stability": stability, "similarity_boost": 0.75}}
    if context[0]: req["previous_text"] = context[0]
    if context[1]: req["next_text"] = context[1]
    if model.endswith("v2_5"): req["language_code"] = LANG  # only the v2.5 models accept a forced language
    body = json.dumps(req).encode()
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}?output_format=mp3_44100_128", data=body, method="POST",
        headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg", "User-Agent": "games-kiara/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r: return r.read()

def load_key():
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key and os.path.exists(".env"):
        for line in open(".env", encoding="utf-8-sig"):
            k, _, v = line.partition("=")
            if k.strip() == "ELEVENLABS_API_KEY": key = v.strip().strip("'\"")
    key = key or getpass.getpass("Paste ElevenLabs API key (hidden): ")
    key = "".join(c for c in key if c.isprintable()).strip()  # Ctrl+V into getpass on Windows can insert control chars
    print(f"Using key {key[:3]}...{key[-2:]} ({len(key)} chars)")
    if not key.startswith("sk_"): sys.exit("That is not an API key (it should start with 'sk_'). The key ID shown in the dashboard won't work.")
    return key

def preview(key, out="audio_preview"):
    os.makedirs(out, exist_ok=True)
    rows = []
    for d, cands in PREVIEW.items():
        cells = []
        for n, c in enumerate(cands, 1):
            text, model, stab = (c + (MODEL, 0.55)[len(c) - 1:])[:3] if isinstance(c, tuple) else (c, MODEL, 0.55)
            name, label = f"{slug(d)}-{n}.mp3", text + ("" if model == MODEL else f" ({model}, stability {stab})")
            try: open(os.path.join(out, name), "wb").write(tts(key, text, model, stab))
            except urllib.error.HTTPError as e: print(f"{d} [{n}] skipped: {e.code} {e.read().decode(errors='ignore')[:150]}"); continue
            print(f"{d} [{n}] {label}"); time.sleep(0.3)
            cells.append(f'<div class="v"><b>{n}</b> <code>{label}</code><audio controls preload="none" src="{name}"></audio></div>')
        rows.append(f'<section><h2>{d}</h2>{"".join(cells)}</section>')
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(
        '<!doctype html><meta charset="utf-8"><title>Preview suara</title><style>body{font-family:sans-serif;max-width:760px;margin:20px auto;padding:0 16px}'
        'section{border-bottom:1px solid #ddd;padding:8px 0}h2{font-size:18px;margin:6px 0}.v{display:flex;align-items:center;gap:10px;margin:4px 0}'
        'code{min-width:220px}</style><h1>Pilih versi terbaik</h1>' + "".join(rows))
    print(f"Open {out}/index.html")

def main():
    test, force = "--test" in sys.argv, "--force" in sys.argv
    only = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--only=")), None)
    items = [x for x in phrases() if x[0] in TEST] if test else phrases()
    if only:
        want = {slug(w) for w in only.split(",")}
        items = [x for x in items if slug(x[0]) in want]; force = True
        if unknown := want - {slug(x[0]) for x in items}: print("Unknown phrases:", ", ".join(sorted(unknown)))
    key = load_key()
    if "--preview" in sys.argv: return preview(key)
    os.makedirs(OUT, exist_ok=True)
    todo = [x for x in items if force or not os.path.exists(os.path.join(OUT, slug(x[0]) + ".mp3"))]
    print(f"{len(items)} phrases, {len(todo)} to generate, ~{sum(len(s) for _, s in todo)} characters")
    for i, (d, s) in enumerate(todo, 1):
        path = os.path.join(OUT, slug(d) + ".mp3")
        try: data = tts(key, s, context=CONTEXT.get(d, (None, None)))
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="ignore")[:300]
            print(f"ERROR {e.code} on '{d}': {msg}")
            if e.code in (401, 402, 403, 429) or "<html" in msg or "authentication_error" in msg: sys.exit("Stopping: malformed request (check the API key)." if "<html" in msg else 1)
            continue
        open(path, "wb").write(data); print(f"[{i}/{len(todo)}] {path}"); time.sleep(0.3)
    print("Done.")

if __name__ == "__main__": main()
