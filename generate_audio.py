import os, re, sys, json, time, getpass, urllib.request, urllib.error
VOICE_ID = "d15jrIAARvF899pDoC6T"
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
TOGGLES = ["kalung","topi","kacamata","payung","syal","jaket","jas hujan","sepatu bot"]
TEST = ["A. Apel","Cari huruf B","Cari huruf W","Cari angka 7","Dua Belas","Cari Kucing","Pintar! Pakai payung supaya tidak basah."]

def slug(t): return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")

def phrases():
    p = []
    for l, w in HURUF: p += [(f"{l}. {w}", f"{LETTER_SAY[l]}. {w}"), (f"Cari huruf {l}", f"Cari huruf {LETTER_SAY[l]}")]
    for i, w in enumerate(ANGKA, 1): p += [(w, w), (f"Cari angka {i}", f"Cari angka {w.lower()}")]
    for h in HEWAN: p += [(h, h), (f"Cari {h}", f"Cari {h}")]
    for c in COLORS:
        for t in ["sepatu","tas","mahkota"]: p += [(f"Gaun Putri warna {c}. Cari {t} warna {c}!",)*2, (f"Pintar! {t.capitalize()} {c}, sama dengan gaunnya!",)*2]
    for say, why, items in WEATHER.values():
        p.append((f"{say} Putri pakai apa ya?",)*2)
        for it in items: p.append((f"Pintar! Pakai {it} {WHY.get(it, why)}.",)*2)
    for n in NAMES: p += [(f"Cari {n}!",)*2, (f"Pintar! Ini {n}.",)*2]
    for lab in ["Gaun","Rok","Sepatu","Mahkota","Tas"]: p += [(f"{lab} {c}",)*2 for c in COLORS]
    p += [(t, t) for t in TOGGLES] + [("Ayo dandani Putri!",)*2, ("Wah, Putri cantik sekali!",)*2]
    seen, out = set(), []
    for d, s in p:
        if slug(d) not in seen: seen.add(slug(d)); out.append((d, s))
    return out

def tts(key, text):
    body = json.dumps({"text": text, "model_id": MODEL, "language_code": LANG, "voice_settings": {"stability": 0.55, "similarity_boost": 0.75}}).encode()
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

def main():
    test, force = "--test" in sys.argv, "--force" in sys.argv
    only = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--only=")), None)
    items = [x for x in phrases() if x[0] in TEST] if test else phrases()
    if only:
        want = {slug(w) for w in only.split(",")}
        items = [x for x in items if slug(x[0]) in want]; force = True
        if unknown := want - {slug(x[0]) for x in items}: print("Unknown phrases:", ", ".join(sorted(unknown)))
    key = load_key()
    os.makedirs(OUT, exist_ok=True)
    todo = [x for x in items if force or not os.path.exists(os.path.join(OUT, slug(x[0]) + ".mp3"))]
    print(f"{len(items)} phrases, {len(todo)} to generate, ~{sum(len(s) for _, s in todo)} characters")
    for i, (d, s) in enumerate(todo, 1):
        path = os.path.join(OUT, slug(d) + ".mp3")
        try: data = tts(key, s)
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="ignore")[:300]
            print(f"ERROR {e.code} on '{d}': {msg}")
            if e.code in (401, 402, 403, 429) or "<html" in msg or "authentication_error" in msg: sys.exit("Stopping: malformed request (check the API key)." if "<html" in msg else 1)
            continue
        open(path, "wb").write(data); print(f"[{i}/{len(todo)}] {path}"); time.sleep(0.3)
    print("Done.")

if __name__ == "__main__": main()
