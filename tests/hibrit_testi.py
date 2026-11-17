#!/usr/bin/env python3
"""
ReForm — Hibrit (klasik + YZ) bölütlemenin tarayıcıda, uygulamanın kendi koduyla testi.

Uygulama dosyası (ReForm_MVP.html) gerçek bir Chrome/Chromium içinde açılır; her test görüntüsü
uygulamadaki ReformAI.analyze fonksiyonuna verilir. Böylece uygulamada gömülü YZ modeli (U²-Net,
onnxruntime-web) ve karar kuralı birebir ölçülür. Ağ bağlantısı gerekmez.

Kurulum (bir kez):
    pip install playwright pillow numpy
    playwright install chromium
    node tests/goruntu_isleme_testi.js --export tests/senaryolar

Çalıştırma:
    python tests/hibrit_testi.py tests/senaryolar --md HIBRIT_TEST_SONUCLARI.md
    (Bilgisayardaki Chrome'u kullanmak için: --chrome "C:/Program Files/Google/Chrome/Application/chrome.exe")
"""
import argparse
import asyncio
import base64
import io
import json
import os
import pathlib

import numpy as np
from PIL import Image

MODES = [('classic', 'Yalnız klasik'), ('auto', 'Otomatik (hibrit)'), ('ai', 'Her zaman YZ')]

PAGE_HELPER = """
async ({png, w, h, mode}) => {
  const img = new Image(); img.src = 'data:image/png;base64,' + png; await img.decode();
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const g = c.getContext('2d'); g.drawImage(img, 0, 0);
  const data = g.getImageData(0, 0, w, h);
  const options = { widthMm: 300, heightMm: 200, threshold: 45, minAreaMm2: 60 };
  const t0 = performance.now();
  const r = await window.ReformAI.analyze(data, options, mode);
  const ms = performance.now() - t0;
  let bin = ''; const b = r.scene.binary;
  for (let i = 0; i < b.length; i += 8192) bin += String.fromCharCode.apply(null, b.subarray(i, i + 8192));
  return { mask: btoa(bin), found: r.scene.components.length, method: r.method, usedAI: r.usedAI, ms,
           bbox: r.scene.components[0] ? r.scene.components[0].bbox : null };
}
"""


async def main(folder, html, md, chrome):
    from playwright.async_api import async_playwright
    reform = json.load(open(os.path.join(folder, 'reform_sonuclar.json'), encoding='utf-8'))
    async with async_playwright() as p:
        kw = {'args': ['--no-sandbox']}
        if chrome:
            kw['executable_path'] = chrome
        browser = await p.chromium.launch(**kw)
        page = await browser.new_page()
        await page.goto(pathlib.Path(html).resolve().as_uri())
        await page.wait_for_function('window.ReformAI && window.ReformAI.available()')
        # Isınma: modeli bir kez yükle (ilk yükleme süresi ayrıca raporlanır).
        warm = await page.evaluate("""async () => { const t0 = performance.now();
            const d = new ImageData(64, 64); await window.ReformAI.segment(d); return performance.now() - t0; }""")
        rows = []
        for r in reform:
            img = Image.open(os.path.join(folder, r['id'] + '_goruntu.ppm')).convert('RGB')
            truth = np.array(Image.open(os.path.join(folder, r['id'] + '_dogru_maske.pgm'))) > 127
            buf = io.BytesIO(); img.save(buf, 'PNG')
            png = base64.b64encode(buf.getvalue()).decode()
            row = {'id': r['id'], 'name': r['name'], 'parts': r['parts']}
            for mode, _ in MODES:
                res = await page.evaluate(PAGE_HELPER, {'png': png, 'w': img.width, 'h': img.height, 'mode': mode})
                pred = np.frombuffer(base64.b64decode(res['mask']), dtype=np.uint8).reshape(truth.shape) > 0
                union = np.logical_or(pred, truth).sum()
                iou = 1.0 if union == 0 else np.logical_and(pred, truth).sum() / union
                row[mode] = {**res, 'iou': float(iou), 'ok': bool(iou >= 0.95 and res['found'] == r['parts'])}
            rows.append(row)
            print(r['id'], r['name'], {m: (round(row[m]['iou'], 3), row[m]['found']) for m, _ in MODES})
        await browser.close()

    f = lambda x: f"{x:.3f}".replace('.', ',')
    lines = ['# ReForm — Hibrit (klasik + YZ) test sonuçları', '',
             'Uygulamanın kendisi (ReForm_MVP.html) Chrome içinde çalıştırıldı; YZ modeli uygulamaya gömülü U²-Net (u2netp) ve onnxruntime-web.',
             f'Görüntü 900 × 600 px = 300 × 200 mm (3 px/mm). Ölçüt: IoU ≥ 0,95 ve parça sayısı doğru. YZ modelinin ilk yüklenmesi: {round(warm)} ms (yalnız bir kez).', '',
             'Hücrelerde: sonuç · IoU · bulunan parça · süre (ms).', '',
             '| # | Senaryo | Beklenen parça | ' + ' | '.join(n for _, n in MODES) + ' | Otomatik modda kullanılan yöntem |',
             '|---|---|---|' + '---|' * len(MODES) + '---|']
    for row in rows:
        cells = [f"{'✓' if row[m]['ok'] else '✗'} {f(row[m]['iou'])} · {row[m]['found']} · {round(row[m]['ms'])}" for m, _ in MODES]
        lines.append(f"| {int(row['id'])} | {row['name']} | {row['parts']} | " + ' | '.join(cells) + f" | {row['auto']['method']} |")
    lines += ['', '| Mod | Başarılı senaryo | Ortalama IoU | Ortanca süre (ms) | YZ kullanılan senaryo |', '|---|---|---|---|---|']
    for m, n in MODES:
        passed = sum(row[m]['ok'] for row in rows)
        lines.append(f"| {n} | {passed} / {len(rows)} | {f(np.mean([row[m]['iou'] for row in rows]))} | "
                     f"{round(float(np.median([row[m]['ms'] for row in rows])))} | {sum(row[m]['usedAI'] for row in rows)} |")
    out = '\n'.join(lines) + '\n'
    print(out)
    if md:
        open(md, 'w', encoding='utf-8').write(out)
        print('Yazıldı:', md)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('klasor', help='node tests/goruntu_isleme_testi.js --export ile üretilen klasör')
    ap.add_argument('--html', default=str(pathlib.Path(__file__).resolve().parent.parent / 'ReForm_MVP.html'))
    ap.add_argument('--md', help='Sonuç tablosunun yazılacağı Markdown dosyası')
    ap.add_argument('--chrome', help='Chrome / Chromium çalıştırılabilir dosyasının yolu (isteğe bağlı)')
    a = ap.parse_args()
    asyncio.run(main(a.klasor, a.html, a.md, a.chrome))
