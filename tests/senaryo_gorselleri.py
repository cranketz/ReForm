#!/usr/bin/env python3
"""
ReForm — 17 test senaryosunun görsellerini üretir.

Her senaryo için üç görüntü yan yana: test görüntüsü · klasik yöntemin sonucu · hibrit (klasik + YZ) yöntemin sonucu.
Renkler: yeşil = doğru bulunan malzeme, kırmızı = yanlışlıkla malzeme sanılan, mavi = kaçırılan malzeme.

Önce senaryoları ve maskeleri üretin:
    node tests/goruntu_isleme_testi.js --export tests/senaryolar
    python tests/hibrit_testi.py tests/senaryolar --maske-kaydet
Sonra:
    python tests/senaryo_gorselleri.py tests/senaryolar
Çıktı: test_senaryolari/NN_*.png (her senaryo) ve docs/test_senaryolari.png (tek sayfalık özet).
"""
import json
import os
import re
import sys
import unicodedata
from collections import deque

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_PIXELS = 60 * 9  # 60 mm² × (3 piksel/mm)²
INK, MUTED, GOOD, BAD = (24, 62, 53), (102, 124, 90), (46, 125, 50), (198, 40, 40)


def font(size, bold=False):
    for name in (['DejaVuSans-Bold.ttf', 'arialbd.ttf'] if bold else ['DejaVuSans.ttf', 'arial.ttf']):
        for base in ('/usr/share/fonts/truetype/dejavu', 'C:/Windows/Fonts', ''):
            try:
                return ImageFont.truetype(os.path.join(base, name) if base else name, size)
            except OSError:
                pass
    return ImageFont.load_default()


def count_parts(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    parts = 0
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        q = deque([(y0, x0)]); seen[y0, x0] = True; n = 0
        while q:
            y, x = q.popleft(); n += 1
            for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True; q.append((yy, xx))
        parts += n >= MIN_PIXELS
    return parts


def overlay(image, pred, truth):
    base = np.asarray(image, np.float32) * 0.45 + 255 * 0.55 * 0.35
    out = base.copy()
    for m, color in ((pred & truth, (60, 170, 80)), (pred & ~truth, (220, 50, 50)), (~pred & truth, (40, 110, 220))):
        out[m] = base[m] * 0.35 + np.array(color) * 0.65
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))


def slug(text):
    text = unicodedata.normalize('NFKD', text.replace('ı', 'i').replace('İ', 'I')).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '_', text).strip('_')[:40]


def main(folder):
    rows = json.load(open(os.path.join(folder, 'reform_sonuclar.json'), encoding='utf-8'))
    out_dir = os.path.join(ROOT, 'test_senaryolari'); os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'docs'), exist_ok=True)
    tiles = []
    for r in rows:
        img = Image.open(os.path.join(folder, r['id'] + '_goruntu.ppm')).convert('RGB')
        truth = np.array(Image.open(os.path.join(folder, r['id'] + '_dogru_maske.pgm'))) > 127
        classic = np.array(Image.open(os.path.join(folder, r['id'] + '_reform_maske.pgm'))) > 127
        hybrid = np.array(Image.open(os.path.join(folder, r['id'] + '_hibrit_maske.png'))) > 127
        res = {}
        for key, m in (('Klasik', classic), ('Hibrit', hybrid)):
            union = (m | truth).sum(); iou = 1.0 if not union else (m & truth).sum() / union
            found = r['found'] if key == 'Klasik' else count_parts(m)
            res[key] = (iou, found, iou >= 0.95 and found == r['parts'])
        # Tek senaryo: üç panel
        W, H, top, bottom = 450, 300, 58, 44
        sheet = Image.new('RGB', (3 * W + 40, H + top + bottom), 'white'); d = ImageDraw.Draw(sheet)
        d.text((10, 12), f"{int(r['id'])}. {r['name']}", font=font(22, True), fill=INK)
        lx = 3 * W + 30
        for txt, col in (('mavi: kaçırılan', (40, 110, 220)), ('kırmızı: fazladan', (220, 50, 50)), ('yeşil: doğru', (60, 170, 80))):
            lx -= int(d.textlength(txt, font=font(15))) + 34
            d.rectangle([lx, 18, lx + 14, 32], fill=col); d.text((lx + 20, 15), txt, font=font(15), fill=MUTED)
        panels = [('Test görüntüsü', img.resize((W, H)), None),
                  ('Klasik yöntem', overlay(img, classic, truth).resize((W, H)), res['Klasik']),
                  ('Hibrit (klasik + YZ)', overlay(img, hybrid, truth).resize((W, H)), res['Hibrit'])]
        for i, (label, im, rr) in enumerate(panels):
            x = 10 + i * (W + 10); sheet.paste(im, (x, top))
            if rr is None:
                d.text((x, top + H + 10), f"Beklenen: {r['parts']} parça", font=font(17), fill=MUTED)
            else:
                iou, found, ok = rr
                d.text((x, top + H + 10), f"{label}: {'✓' if ok else '✗'}  IoU {iou:.3f}  ·  {found} parça".replace('.', ','),
                       font=font(17, True), fill=GOOD if ok else BAD)
        name = f"{r['id']}_{slug(r['name'])}.png"
        sheet.save(os.path.join(out_dir, name), optimize=True)
        tiles.append((r, img, res))
        print(name)
    # Özet: 4 sütun
    cols, tw, th, cap = 4, 420, 280, 74
    n_rows = (len(tiles) + cols - 1) // cols
    head = 120
    over = Image.new('RGB', (cols * (tw + 16) + 16, head + n_rows * (th + cap + 16)), 'white'); d = ImageDraw.Draw(over)
    d.text((16, 16), 'ReForm · 17 test senaryosu', font=font(32, True), fill=INK)
    k = sum(t[2]['Klasik'][2] for t in tiles); h = sum(t[2]['Hibrit'][2] for t in tiles)
    d.text((16, 62), f'Başarı (IoU ≥ 0,95 ve parça sayısı doğru): yalnız klasik {k}/17 · hibrit {h}/17.  '
                     'Ayrıntılı üç panelli görseller: test_senaryolari/', font=font(18), fill=MUTED)
    for i, (r, img, res) in enumerate(tiles):
        x = 16 + (i % cols) * (tw + 16); y = head + (i // cols) * (th + cap + 16)
        over.paste(img.resize((tw, th)), (x, y))
        name = f"{int(r['id'])}. {r['name']}"
        if len(name) > 44:
            name = name[:43] + '…'
        d.text((x, y + th + 6), name, font=font(16, True), fill=INK)
        for j, key in enumerate(('Klasik', 'Hibrit')):
            ok = res[key][2]
            d.text((x + j * 150, y + th + 32), f"{key}: {'✓' if ok else '✗'}", font=font(17, True), fill=GOOD if ok else BAD)
    over.save(os.path.join(ROOT, 'docs', 'test_senaryolari.png'), optimize=True)
    print('docs/test_senaryolari.png', f'klasik {k}/17, hibrit {h}/17')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    main(sys.argv[1])
