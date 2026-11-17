"""Gerçekçi ReForm test fotoğrafları: bilinen mm ölçüleri, eğik çekim, doku, gölge, ışık, gürültü, JPEG.

Kullanım:  pip install numpy pillow  →  python tests/test_fotografi_uret.py
Çıktı:     test_fotograflari/01…10_*.jpg ve cevap.json (gerçek ölçüler, pano köşelerinin piksel konumları)
Fotoğraflar her çalıştırmada aynı çıkar (sabit rastgelelik tohumu).
"""
import json, math, os, zlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

PX = 4                      # pano üzerinde 4 piksel / mm
BW, BH = 300, 200           # pano (çekim alanı) 300 × 200 mm → uygulamadaki varsayılan "30 × 20 cm"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'test_fotograflari')
os.makedirs(OUT, exist_ok=True)


def grid(h, w):
    return np.mgrid[0:h, 0:w].astype(np.float32)


def smooth_noise(h, w, scale, rng):
    small = rng.random((max(2, h // scale + 2), max(2, w // scale + 2))).astype(np.float32)
    img = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(img, np.float32) / 255


def wood(h, w, base, rng, angle=0.2, ring=3.2):
    y, x = grid(h, w)
    a = math.radians(angle * 57)
    u = x * math.cos(a) + y * math.sin(a)
    v = -x * math.sin(a) + y * math.cos(a)
    warp = 14 * smooth_noise(h, w, 90, rng) + 6 * np.sin(u / 160)
    grain = np.sin((v + warp * 6) / ring) * 0.5 + 0.5
    fine = smooth_noise(h, w, 6, rng)
    t = 0.80 + 0.14 * grain + 0.08 * fine
    return np.clip(np.array(base, np.float32)[None, None, :] * t[..., None], 0, 255)


def flat(h, w, base, rng, amount=6, scale=8):
    n = (smooth_noise(h, w, scale, rng) - 0.5) * 2 * amount + (rng.random((h, w)) - 0.5) * amount
    return np.clip(np.array(base, np.float32)[None, None, :] + n[..., None], 0, 255)


def board_texture(kind, rng):
    h, w = BH * PX, BW * PX
    if kind == 'koyu':
        return flat(h, w, (38, 44, 52), rng, 5, 30)
    if kind == 'beyaz':
        return flat(h, w, (238, 237, 232), rng, 3, 40)
    if kind == 'acik_gri':
        return flat(h, w, (214, 214, 210), rng, 4, 40)
    if kind == 'kesim_mati':
        img = flat(h, w, (36, 112, 84), rng, 5, 30)
        y, x = grid(h, w)
        for step, width, alpha in ((10, 0.35, 0.55), (50, 0.7, 0.8)):
            d = np.minimum(np.abs((x / PX) % step - 0), np.abs(step - (x / PX) % step))
            e = np.minimum(np.abs((y / PX) % step - 0), np.abs(step - (y / PX) % step))
            line = np.clip(1 - np.minimum(d, e) / width, 0, 1) * alpha
            img = img * (1 - line[..., None]) + np.array([205, 230, 215])[None, None, :] * line[..., None]
        return img
    raise ValueError(kind)


def raster(polys, holes=(), ellipses_holes=()):
    """mm cinsinden çokgenler → 4 px/mm maske (2× örnekleme ile yumuşak kenar)."""
    S = 2
    m = Image.new('L', (BW * PX * S, BH * PX * S), 0)
    d = ImageDraw.Draw(m)
    for p in polys:
        d.polygon([(x * PX * S, y * PX * S) for x, y in p], fill=255)
    for p in holes:
        d.polygon([(x * PX * S, y * PX * S) for x, y in p], fill=0)
    for (cx, cy, r) in ellipses_holes:
        d.ellipse([(cx - r) * PX * S, (cy - r) * PX * S, (cx + r) * PX * S, (cy + r) * PX * S], fill=0)
    m = m.resize((BW * PX, BH * PX), Image.LANCZOS)
    return np.asarray(m, np.float32) / 255


def shadow(mask, dx, dy, blur_mm, strength):
    img = Image.fromarray((mask * 255).astype(np.uint8))
    img = img.transform(img.size, Image.AFFINE, (1, 0, -dx * PX, 0, 1, -dy * PX))
    img = img.filter(ImageFilter.GaussianBlur(blur_mm * PX))
    return 1 - strength * np.asarray(img, np.float32) / 255


def perspective_coeffs(dst, src):
    """PIL PERSPECTIVE katsayıları: çıktı (dst) noktası → girdi (src) noktası."""
    A, b = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    return np.linalg.solve(np.array(A, float), np.array(b, float)).tolist()


def compose(board, corners, rng, table='masa', size=(2400, 1800), light=(0.25, 0.0), vignette=0.25, noise=4.0, blur=0.7, quality=86):
    W, H = size
    if table == 'masa':
        bg = wood(H, W, (150, 120, 92), rng, angle=0.02, ring=9)
    else:
        bg = flat(H, W, (120, 124, 130), rng, 6, 50)
    bw, bh = board.shape[1], board.shape[0]
    src = [(0, 0), (bw, 0), (bw, bh), (0, bh)]
    coeffs = perspective_coeffs(corners, src)
    bimg = Image.fromarray(board.astype(np.uint8)).transform((W, H), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    alpha = Image.new('L', (bw, bh), 255).transform((W, H), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    # Panonun masaya düşen gölgesi
    sh = alpha.filter(ImageFilter.GaussianBlur(18))
    sh = np.asarray(sh.transform((W, H), Image.AFFINE, (1, 0, -10, 0, 1, -14)), np.float32) / 255
    bg = bg * (1 - 0.35 * sh[..., None])
    a = np.asarray(alpha, np.float32)[..., None] / 255
    img = bg * (1 - a) + np.asarray(bimg, np.float32) * a
    # Işık eğimi + kenar kararması + sensör gürültüsü
    y, x = grid(H, W)
    gx, gy = light
    img *= (1 + gx * (x / W - 0.5) + gy * (y / H - 0.5))[..., None]
    r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    img *= (1 - vignette * np.clip(r - 0.35, 0, 1) ** 2)[..., None]
    img += rng.normal(0, noise, img.shape)
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    if blur:
        out = out.filter(ImageFilter.GaussianBlur(blur))
    return out, quality


def place(board, mask, tex, shadow_cfg=None):
    if shadow_cfg:
        board = board * shadow(mask, *shadow_cfg)[..., None]
    return board * (1 - mask[..., None]) + tex * mask[..., None]


def measure(mask):
    ys, xs = np.nonzero(mask > 0.5)
    return {'en_mm': round((xs.max() - xs.min() + 1) / PX, 1), 'boy_mm': round((ys.max() - ys.min() + 1) / PX, 1),
            'alan_mm2': round(float((mask > 0.5).sum()) / PX ** 2),
            '_kutu': [xs.min() / PX, ys.min() / PX, (xs.max() + 1) / PX, (ys.max() + 1) / PX]}


def rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def rot(poly, deg, cx, cy):
    a = math.radians(deg)
    return [(cx + (x - cx) * math.cos(a) - (y - cy) * math.sin(a), cy + (x - cx) * math.sin(a) + (y - cy) * math.cos(a)) for x, y in poly]


PLY, MDF, CARD, FELT = (196, 156, 108), (139, 98, 66), (236, 232, 222), (178, 44, 52)
scenes = []


def scene(name, title, expect, board_kind, pieces, corners, **photo):
    rng = np.random.default_rng(zlib.crc32(name.encode()))
    board = board_texture(board_kind, rng)
    truth = []
    for pc in pieces:
        m = raster(pc['polys'], pc.get('holes', ()), pc.get('circles', ()))
        kind = pc['tex']
        h, w = m.shape
        tex = {'ply': lambda: wood(h, w, PLY, rng, pc.get('angle', 0.1)), 'mdf': lambda: flat(h, w, MDF, rng, 7, 3),
               'card': lambda: flat(h, w, CARD, rng, 3, 4), 'felt': lambda: flat(h, w, FELT, rng, 12, 2)}[kind]()
        board = place(board, m, tex, pc.get('shadow', (1.2, 1.6, 1.2, 0.45)))
        truth.append({'ad': pc['ad'], **measure(m), 'delik': pc.get('delik', '')})
    img, q = compose(board, corners, rng, **photo)
    path = os.path.join(OUT, name + '.jpg')
    img.save(path, quality=q)
    kutu = [min(t['_kutu'][0] for t in truth), min(t['_kutu'][1] for t in truth), max(t['_kutu'][2] for t in truth), max(t['_kutu'][3] for t in truth)]
    genel = {'en_mm': round(kutu[2] - kutu[0], 1), 'boy_mm': round(kutu[3] - kutu[1], 1)}
    for t in truth: t.pop('_kutu')
    scenes.append({'genel': genel, 'dosya': name + '.jpg', 'baslik': title, 'beklenen': expect, 'zemin': board_kind,
                   'kose_piksel': [[round(x), round(y)] for x, y in corners], 'parcalar': truth,
                   'foto': {'boyut': list(img.size), **{k: v for k, v in photo.items() if k != 'table'}}})


# 1 — Kolay: koyu pano, tek L parça, hafif açı
L = [(60, 50), (200, 50), (200, 95), (125, 95), (125, 160), (60, 160)]
scene('01_kolay_koyu_zemin', 'Koyu zemin, L biçimli kontrplak, hafif açı', 'Klasik yöntem bulmalı (1 parça).', 'koyu',
      [{'ad': 'L kontrplak', 'tex': 'ply', 'polys': [L]}], [(420, 330), (1990, 360), (1960, 1420), (440, 1400)])
# 2 — Eğik çekim
scene('02_egik_cekim', 'Güçlü eğik açıdan çekim (perspektif)', 'Köşeler seçilince ölçü düzelmeli (1 parça).', 'koyu',
      [{'ad': 'Kontrplak levha', 'tex': 'ply', 'polys': [rot(rect(70, 45, 160, 105), 8, 150, 100)]}],
      [(640, 420), (1830, 520), (2180, 1500), (210, 1380)], light=(0.15, 0.1))
# 3 — İki MDF parça, yandan ışık
scene('03_iki_mdf_yan_isik', 'İki ayrı MDF parça, yandan gelen ışık', 'Klasik yöntem 2 parça bulmalı.', 'koyu',
      [{'ad': 'MDF A', 'tex': 'mdf', 'polys': [rect(30, 40, 110, 120)]},
       {'ad': 'MDF B', 'tex': 'mdf', 'polys': [[(170, 35), (270, 50), (262, 150), (185, 165)]]}],
      [(380, 300), (2020, 330), (2010, 1440), (390, 1420)], light=(0.45, 0.05))
# 4 — Delikli parça
scene('04_delikli_parca', 'Kontrplakta yuvarlak ve dikdörtgen delik', 'Klasik yöntem 1 parça + 2 delik bulmalı.', 'koyu',
      [{'ad': 'Delikli kontrplak', 'tex': 'ply', 'polys': [rect(40, 30, 220, 140)], 'holes': [rect(170, 65, 55, 40)],
        'circles': [(100, 100, 25)], 'delik': 'Ø50 mm daire + 55 × 40 mm dikdörtgen'}],
      [(410, 320), (2000, 345), (1985, 1430), (425, 1410)])
# 5 — Beyaz zeminde beyaz karton (YZ)
scene('05_beyaz_zemin_beyaz_karton', 'Beyaz kağıt üzerinde beyaz karton', 'Klasik yöntem bulamaz → otomatik modda YZ devreye girmeli.', 'beyaz',
      [{'ad': 'Beyaz karton', 'tex': 'card', 'polys': [[(60, 40), (230, 55), (240, 150), (75, 165)]], 'shadow': (0.6, 0.8, 0.8, 0.12)}],
      [(430, 330), (1985, 350), (1975, 1420), (445, 1405)], table='gri')
# 6 — Kesim matı (YZ)
scene('06_kesim_mati', 'Yeşil kareli kesim matı üzerinde kontrplak', 'Klasik yöntem çok parça bulur → otomatik modda YZ devreye girmeli.', 'kesim_mati',
      [{'ad': 'Kontrplak', 'tex': 'ply', 'polys': [rect(80, 50, 140, 100)]}],
      [(400, 320), (2000, 340), (1990, 1430), (410, 1415)])
# 7 — Açık zeminde güçlü gölge (beklenen hata)
scene('07_acik_zemin_golge', 'Açık gri zemin, sert gölge', 'Beklenen hata: gölge parçaya eklenir, ölçü büyük çıkar.', 'acik_gri',
      [{'ad': 'MDF', 'tex': 'mdf', 'polys': [rect(70, 45, 140, 100)], 'shadow': (8, 6, 1.0, 0.55)}],
      [(420, 330), (1990, 350), (1980, 1425), (435, 1410)], table='gri')
# 8 — Birbirine değen parçalar (beklenen hata)
scene('08_degen_parcalar', 'Birbirine değen iki kontrplak parça', 'Beklenen hata: 2 parça yerine 1 parça bulunur.', 'koyu',
      [{'ad': 'Kontrplak A', 'tex': 'ply', 'polys': [rect(40, 40, 110, 120)]},
       {'ad': 'Kontrplak B (A’ya değiyor)', 'tex': 'ply', 'polys': [rect(150, 70, 110, 80)], 'angle': 1.3}],
      [(415, 325), (1995, 345), (1985, 1425), (430, 1410)])
# 9 — Kırmızı keçe, düzensiz biçim, hafif bulanık
blob = [(150 + (70 + 18 * math.sin(3 * t) + 8 * math.cos(5 * t)) * math.cos(t), 100 + (55 + 12 * math.sin(2 * t + 1)) * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 90, endpoint=False)]
scene('09_kece_duzensiz', 'Kırmızı keçe, düzensiz kenar, hafif bulanık', 'Klasik yöntem bulmalı (1 parça).', 'koyu',
      [{'ad': 'Kırmızı keçe', 'tex': 'felt', 'polys': [blob], 'shadow': (1, 1.2, 1.5, 0.35)}],
      [(430, 330), (1985, 350), (1975, 1420), (440, 1405)], blur=1.6)
# 10 — Çok sayıda küçük artık
small = [rect(25, 25, 60, 45), rect(110, 30, 35, 70), rot(rect(170, 30, 90, 40), -12, 215, 50), rect(30, 115, 80, 55),
         [(150, 120), (235, 110), (265, 170), (160, 175)], rect(272, 92, 6, 6)]
scene('10_kucuk_artiklar', 'Altı küçük kontrplak artığı (biri 6 × 6 mm)', '5 parça bulunmalı; 6 × 6 mm (36 mm²) parça 60 mm² sınırının altında kaldığı için atılmalı.', 'koyu',
      [{'ad': f'Artık {i + 1}', 'tex': 'ply', 'polys': [p], 'angle': 0.1 + i * 0.3} for i, p in enumerate(small)],
      [(420, 325), (1990, 345), (1980, 1425), (435, 1410)])

json.dump(scenes, open(os.path.join(OUT, 'cevap.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok', len(scenes))
