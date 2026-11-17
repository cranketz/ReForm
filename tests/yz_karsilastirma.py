#!/usr/bin/env python3
"""
ReForm — Klasik görüntü işleme ile YZ tabanlı arka plan çıkarmanın karşılaştırılması.

Karşılaştırılan yöntemler
  * ReForm      : uygulamadaki renk farkı + bağlı bileşen yöntemi (sonuçlar Node test betiğinden gelir)
  * rembg u2netp: U²-Net'in küçük sürümü (4,6 MB), genel amaçlı "öne çıkan nesne" bölütleme modeli
  * rembg u2net : U²-Net tam sürüm (176 MB)

Kurulum (bir kez):
    pip install "rembg[cpu]" pillow numpy
    node tests/goruntu_isleme_testi.js --export tests/senaryolar

Çalıştırma:
    python tests/yz_karsilastirma.py tests/senaryolar --md YZ_KARSILASTIRMA.md
    python tests/yz_karsilastirma.py tests/senaryolar --modeller u2netp          (yalnız küçük model)

Gerçek fotoğraflarla görsel karşılaştırma (doğru maske gerekmez):
    python tests/yz_karsilastirma.py --fotograflar fotograflarim/ --cikti karsilastirma/
    Her fotoğraf için rembg maskesini kaydeder; aynı fotoğrafın ReForm sonucuyla yan yana koyup inceleyin.

Not: Modeller ilk çalıştırmada internetten indirilir; sonrası çevrim dışı çalışır.
"""
import argparse
import json
import os
import sys
import time

import numpy as np
from PIL import Image

THRESHOLD = 128  # rembg alfa maskesi 0-255; yarısı ve üstü "nesne" kabul edilir


def iou(pred, truth):
    union = np.logical_or(pred, truth).sum()
    return 1.0 if union == 0 else np.logical_and(pred, truth).sum() / union


def count_parts(mask, min_pixels):
    """4-komşuluk bağlı bileşen sayısı (ReForm ile aynı kural, en küçük alan filtresiyle)."""
    from collections import deque
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
        if n >= min_pixels:
            parts += 1
    return parts


def run_scenarios(folder, models, md_path):
    from rembg import new_session, remove
    reform = json.load(open(os.path.join(folder, 'reform_sonuclar.json'), encoding='utf-8'))
    sessions = {m: new_session(m) for m in models}
    min_pixels = 60 * 9  # 60 mm² × (3 piksel/mm)²
    rows = []
    for r in reform:
        img = Image.open(os.path.join(folder, r['id'] + '_goruntu.ppm')).convert('RGB')
        truth = np.array(Image.open(os.path.join(folder, r['id'] + '_dogru_maske.pgm'))) > 127
        row = {'id': r['id'], 'name': r['name'], 'parts': r['parts'],
               'ReForm': {'iou': r['iou'], 'found': r['found'], 'ms': r['ms']}}
        for m, sess in sessions.items():
            remove(img, session=sess, only_mask=True)  # ısınma
            t0 = time.perf_counter()
            mask = np.array(remove(img, session=sess, only_mask=True)) >= THRESHOLD
            ms = (time.perf_counter() - t0) * 1000
            Image.fromarray((mask * 255).astype('uint8')).save(os.path.join(folder, f"{r['id']}_{m}_maske.png"))
            row[m] = {'iou': float(iou(mask, truth)), 'found': count_parts(mask, min_pixels), 'ms': ms}
        rows.append(row)
        print(r['id'], r['name'], {k: round(v['iou'], 3) for k, v in row.items() if isinstance(v, dict)})

    methods = ['ReForm'] + list(models)
    ok = lambda v, parts: v['iou'] >= 0.95 and v['found'] == parts
    f = lambda x: f"{x:.3f}".replace('.', ',')
    lines = ['# ReForm — Klasik yöntem ile YZ modeli karşılaştırması', '',
             'Aynı yapay test görüntüleri (900 × 600 px, 3 px/mm). Ölçüt: IoU ≥ 0,95 ve parça sayısı doğru.', '',
             'Hücrelerde: IoU · bulunan parça · süre (ms).', '',
             '| # | Senaryo | Beklenen parça | ' + ' | '.join(methods) + ' |',
             '|---|---|---|' + '---|' * len(methods)]
    for row in rows:
        cells = []
        for m in methods:
            v = row[m]
            cells.append(f"{'✓' if ok(v, row['parts']) else '✗'} {f(v['iou'])} · {v['found']} · {round(v['ms'])}")
        lines.append(f"| {int(row['id'])} | {row['name']} | {row['parts']} | " + ' | '.join(cells) + ' |')
    lines += ['', '| Yöntem | Başarılı senaryo | Ortalama IoU | Ortanca süre (ms) | Model boyutu | Çevrim dışı | Ölçek (mm) |',
              '|---|---|---|---|---|---|---|']
    size = {'ReForm': '0 (kod ~40 KB)', 'u2netp': '4,6 MB', 'u2net': '176 MB'}
    for m in methods:
        vals = [row[m] for row in rows]
        passed = sum(ok(row[m], row['parts']) for row in rows)
        lines.append(f"| {m} | {passed} / {len(rows)} | {f(np.mean([v['iou'] for v in vals]))} | "
                     f"{round(float(np.median([v['ms'] for v in vals])))} | {size.get(m, '?')} | "
                     f"{'evet, tarayıcıda' if m == 'ReForm' else 'evet (indirildikten sonra), Python gerekir'} | "
                     f"{'evet, 4 köşe ile' if m == 'ReForm' else 'hayır, yalnız maske verir'} |")
    md = '\n'.join(lines) + '\n'
    print(md)
    if md_path:
        open(md_path, 'w', encoding='utf-8').write(md)
        print('Yazıldı:', md_path)


def run_photos(folder, out, models):
    from rembg import new_session, remove
    os.makedirs(out, exist_ok=True)
    sessions = {m: new_session(m) for m in models}
    for name in sorted(os.listdir(folder)):
        if not name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            continue
        img = Image.open(os.path.join(folder, name)).convert('RGB')
        img.thumbnail((1400, 1400))  # uygulama da 1400 px'e küçültüyor
        for m, sess in sessions.items():
            t0 = time.perf_counter()
            mask = remove(img, session=sess, only_mask=True)
            ms = (time.perf_counter() - t0) * 1000
            base = os.path.splitext(name)[0]
            mask.save(os.path.join(out, f'{base}_{m}_maske.png'))
            print(f'{name}: {m} {ms:.0f} ms')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('klasor', nargs='?', help='node --export ile üretilen senaryo klasörü')
    ap.add_argument('--md', help='Sonuç tablosunu yazılacak Markdown dosyası')
    ap.add_argument('--modeller', nargs='+', default=['u2netp', 'u2net'])
    ap.add_argument('--fotograflar', help='Gerçek fotoğraf klasörü (görsel karşılaştırma)')
    ap.add_argument('--cikti', default='karsilastirma', help='Gerçek fotoğraf maskelerinin yazılacağı klasör')
    a = ap.parse_args()
    if a.fotograflar:
        run_photos(a.fotograflar, a.cikti, a.modeller)
    elif a.klasor:
        run_scenarios(a.klasor, a.modeller, a.md)
    else:
        ap.print_help(); sys.exit(1)
