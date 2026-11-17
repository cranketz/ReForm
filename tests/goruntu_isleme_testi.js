#!/usr/bin/env node
/*
 * ReForm — görüntü işleme (ReformVision) sayısal test betiği.
 *
 * Kullanım (proje klasöründe):   node tests/goruntu_isleme_testi.js
 * İsteğe bağlı:                  node tests/goruntu_isleme_testi.js ReForm_MVP.html --md TEST_SONUCLARI.md
 *                                node tests/goruntu_isleme_testi.js --export tests/senaryolar
 *   --export: her senaryonun görüntüsünü (.ppm) ve doğru maskesini (.pgm) yazar; ReForm sonuçlarını
 *             JSON olarak kaydeder. yz_karsilastirma.py bu klasörü kullanır.
 *
 * Hiçbir ek paket gerekmez. Betik, test edilen kodu kopyalamaz: ReForm_MVP.html içindeki
 * ReformVision modülünü doğrudan okuyup çalıştırır. Böylece uygulamadaki kodun kendisi test edilir.
 *
 * Her senaryoda gerçek (doğru) maske bilinen yapay bir görüntü üretilir ve şu ölçülür:
 *   - IoU (kesişim / birleşim, piksel maskesi)
 *   - bulunan parça sayısı / beklenen parça sayısı
 *   - alan hatası (%)
 *   - en büyük parçanın en ve boy hatası (mm)
 *   - analiz süresi (ms)
 * Başarı ölçütü: IoU >= 0,95 ve parça sayısı doğru.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const args = process.argv.slice(2);
const htmlPath = path.resolve(args.find(a => a.endsWith('.html')) || path.join(__dirname, '..', 'ReForm_MVP.html'));
const mdIndex = args.indexOf('--md');
const mdPath = mdIndex >= 0 ? path.resolve(args[mdIndex + 1]) : null;
const exIndex = args.indexOf('--export');
const exportDir = exIndex >= 0 ? path.resolve(args[exIndex + 1]) : null;
if (exportDir) fs.mkdirSync(exportDir, { recursive: true });
function writePPM(file, image) {
  const header = Buffer.from(`P6\n${image.width} ${image.height}\n255\n`), body = Buffer.alloc(image.width * image.height * 3);
  for (let i = 0, j = 0; i < image.data.length; i += 4) { body[j++] = image.data[i]; body[j++] = image.data[i + 1]; body[j++] = image.data[i + 2]; }
  fs.writeFileSync(file, Buffer.concat([header, body]));
}
function writePGM(file, mask, w, h) {
  const header = Buffer.from(`P5\n${w} ${h}\n255\n`), body = Buffer.alloc(w * h);
  for (let i = 0; i < mask.length; i++) body[i] = mask[i] ? 255 : 0;
  fs.writeFileSync(file, Buffer.concat([header, body]));
}

// --- 1. Uygulamadaki ReformVision modülünü yükle ---------------------------------------------
const html = fs.readFileSync(htmlPath, 'utf8');
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const visionSource = scripts.find(s => s.includes('root.ReformVision = api'));
if (!visionSource) { console.error('ReformVision modülü bulunamadı: ' + htmlPath); process.exit(1); }
const sandbox = { globalThis: {}, Math, Number, Array, Uint8Array, Int32Array, Uint8ClampedArray, Map, Error };
sandbox.window = sandbox.globalThis;
vm.createContext(sandbox);
vm.runInContext(visionSource, sandbox);
const Vision = sandbox.window.ReformVision;
const { performance } = require('perf_hooks');

// --- 2. Yapay görüntü üretimi ------------------------------------------------------------------
// 900 × 600 piksel = 300 × 200 mm çekim alanı → 3 piksel / mm.
const W = 900, H = 600, WIDTH_MM = 300, HEIGHT_MM = 200, PX_PER_MM = W / WIDTH_MM;
let seed = 42;
const rand = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };

const BG_DARK = [30, 45, 60], WOOD = [200, 160, 110];
const rect = (x0, y0, x1, y1) => (x, y) => x >= x0 && x < x1 && y >= y0 && y < y1;
const MAIN = rect(225, 150, 675, 450);              // 150 × 100 mm parça

function render(shape, color) {
  const data = new Uint8ClampedArray(W * H * 4), truth = new Uint8Array(W * H);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const inside = shape(x, y), c = color(x, y, inside), i = (y * W + x) * 4;
    truth[y * W + x] = inside ? 1 : 0;
    data[i] = c[0]; data[i + 1] = c[1]; data[i + 2] = c[2]; data[i + 3] = 255;
  }
  return { image: { data, width: W, height: H }, truth };
}

function boxBlur(image, radius) {
  const { data, width: w, height: h } = image, out = new Uint8ClampedArray(data.length);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    let r = 0, g = 0, b = 0, n = 0;
    for (let dy = -radius; dy <= radius; dy++) for (let dx = -radius; dx <= radius; dx++) {
      const xx = Math.min(w - 1, Math.max(0, x + dx)), yy = Math.min(h - 1, Math.max(0, y + dy)), i = (yy * w + xx) * 4;
      r += data[i]; g += data[i + 1]; b += data[i + 2]; n++;
    }
    const o = (y * w + x) * 4; out[o] = r / n; out[o + 1] = g / n; out[o + 2] = b / n; out[o + 3] = 255;
  }
  return { data: out, width: w, height: h };
}

// --- 3. Senaryolar -----------------------------------------------------------------------------
const scenarios = [
  { name: 'İdeal: koyu düz zemin, açık ahşap', group: 'temel', parts: 1,
    build: () => render(MAIN, (x, y, i) => i ? WOOD : BG_DARK) },
  { name: 'Düşük kontrast: bej zemin, açık ahşap', group: 'renk', parts: 1,
    build: () => render(MAIN, (x, y, i) => i ? [205, 175, 135] : [222, 202, 172]) },
  { name: 'Çok düşük kontrast: beyaz zemin, beyaz karton', group: 'renk', parts: 1,
    build: () => render(MAIN, (x, y, i) => i ? [236, 233, 226] : [246, 246, 246]) },
  { name: 'Işık eğimi: sol kenar %45 karanlık', group: 'ışık', parts: 1,
    build: () => render(MAIN, (x, y, i) => (i ? WOOD : BG_DARK).map(v => v * (0.45 + 0.55 * x / W))) },
  { name: 'Koyu zeminde gölge (parçanın sağında)', group: 'ışık', parts: 1,
    build: () => render(MAIN, (x, y, i) => i ? WOOD : (x >= 675 && x < 705 && y > 165 && y < 465 ? [12, 20, 28] : BG_DARK)) },
  { name: 'Açık zeminde gölge (parçanın sağında)', group: 'ışık', parts: 1,
    build: () => render(MAIN, (x, y, i) => i ? [150, 105, 60] : (x >= 675 && x < 705 && y > 165 && y < 465 ? [150, 150, 150] : [235, 235, 235])) },
  { name: 'Güçlü gürültü (±40)', group: 'kalite', parts: 1,
    build: () => render(MAIN, (x, y, i) => (i ? WOOD : BG_DARK).map(v => v + (rand() - 0.5) * 80)) },
  { name: 'Bulanıklık (7 × 7 piksel ortalama)', group: 'kalite', parts: 1,
    build: () => { const r = render(MAIN, (x, y, i) => i ? WOOD : BG_DARK); r.image = boxBlur(r.image, 3); return r; } },
  { name: 'Ahşap dokusu (damarlı yüzey)', group: 'kalite', parts: 1,
    build: () => render(MAIN, (x, y, i) => i ? WOOD.map(v => v - 35 * (0.5 + 0.5 * Math.sin(y / 6 + Math.sin(x / 40) * 2))) : BG_DARK) },
  { name: 'Delikli parça (ortada 40 mm delik)', group: 'şekil', parts: 1,
    build: () => { const hole = rect(390, 240, 510, 360); return render((x, y) => MAIN(x, y) && !hole(x, y), (x, y, i) => i ? WOOD : BG_DARK); } },
  { name: 'İki ayrı parça', group: 'şekil', parts: 2,
    build: () => { const a = rect(90, 120, 390, 480), b = rect(510, 150, 810, 420); return render((x, y) => a(x, y) || b(x, y), (x, y, i) => i ? WOOD : BG_DARK); } },
  { name: 'Birbirine değen iki parça', group: 'şekil', parts: 2,
    build: () => { const a = rect(150, 150, 450, 450), b = rect(450, 200, 750, 400); return render((x, y) => a(x, y) || b(x, y), (x, y, i) => i ? (x < 450 ? WOOD : [185, 145, 100]) : BG_DARK); } },
  { name: 'Desenli zemin (32 px ≈ 11 mm kareli, kesim matı gibi)', group: 'zemin', parts: 1,
    build: () => render(MAIN, (x, y, i) => i ? WOOD : (((x >> 5) + (y >> 5)) & 1 ? BG_DARK : [90, 100, 110])) },
  { name: 'Kesim matı (yeşil zemin, 10 mm çizgiler)', group: 'zemin', parts: 1,
    build: () => render(MAIN, (x, y, i) => i ? WOOD : (x % 30 < 2 || y % 30 < 2 ? [205, 230, 215] : [36, 112, 84])) },
  { name: 'Desenli zeminde delikli parça', group: 'zemin', parts: 1,
    build: () => { const hole = rect(390, 240, 510, 360); return render((x, y) => MAIN(x, y) && !hole(x, y), (x, y, i) => i ? WOOD : (((x >> 5) + (y >> 5)) & 1 ? BG_DARK : [90, 100, 110])); } },
  { name: 'Masa kenarı görünüyor (köşeler ~2 mm dışarıdan seçilmiş)', group: 'kadraj', parts: 1,
    build: () => render(MAIN, (x, y, i) => i ? WOOD : (x < 6 || y < 6 || x >= W - 6 || y >= H - 6 ? [150, 120, 92] : BG_DARK)) },
  { name: 'Kenara değen parça (kadraj dışına taşıyor)', group: 'kadraj', parts: 1,
    build: () => { const s = rect(600, 150, 900, 450); return render(s, (x, y, i) => i ? WOOD : BG_DARK); } },
];

// --- 4. Perspektif (eğik çekim) testi: homografi ile düzeltme sonrası ölçü hatası -------------
function perspectiveTest() {
  // Gerçek çekim alanı 300 × 200 mm. Eğik fotoğrafta köşeler aşağıdaki piksellerde.
  const corners = [{ x: 160, y: 90 }, { x: 760, y: 130 }, { x: 830, y: 540 }, { x: 90, y: 500 }];
  // Fotoğrafı üretmek için birim kare → köşeler homografisini çöz.
  const A = [], b = [], unit = [[0, 0], [1, 0], [1, 1], [0, 1]];
  for (let i = 0; i < 4; i++) {
    const [u, v] = unit[i], { x, y } = corners[i];
    A.push([u, v, 1, 0, 0, 0, -x * u, -x * v]); b.push(x);
    A.push([0, 0, 0, u, v, 1, -y * u, -y * v]); b.push(y);
  }
  const h = solve(A, b);
  // Ters yön: her foto pikseli için (u, v) bul → gerçek dünya (mm) → parça içinde mi?
  const data = new Uint8ClampedArray(W * H * 4);
  const inv = invert3([[h[0], h[1], h[2]], [h[3], h[4], h[5]], [h[6], h[7], 1]]);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const d = inv[2][0] * x + inv[2][1] * y + inv[2][2];
    const u = (inv[0][0] * x + inv[0][1] * y + inv[0][2]) / d, v = (inv[1][0] * x + inv[1][1] * y + inv[1][2]) / d;
    const mmX = u * WIDTH_MM, mmY = v * HEIGHT_MM, inField = u >= 0 && u <= 1 && v >= 0 && v <= 1;
    const inPart = mmX >= 75 && mmX < 225 && mmY >= 50 && mmY < 150; // 150 × 100 mm
    const c = !inField ? [120, 120, 120] : inPart ? WOOD : BG_DARK, i = (y * W + x) * 4;
    data[i] = c[0]; data[i + 1] = c[1]; data[i + 2] = c[2]; data[i + 3] = 255;
  }
  const t0 = performance.now();
  const flat = Vision.warp({ data, width: W, height: H }, corners, 900, 600);
  const scene = Vision.analyze(flat, { widthMm: WIDTH_MM, heightMm: HEIGHT_MM, threshold: 45, minAreaMm2: 60 });
  const ms = performance.now() - t0, c = scene.components[0];
  return { found: scene.components.length, widthErr: c ? c.bbox.width - 150 : NaN, heightErr: c ? c.bbox.height - 100 : NaN,
           areaErrPct: c ? (c.areaMm2 - 15000) / 15000 * 100 : NaN, ms };
}
function solve(m, r) {
  const n = r.length, a = m.map((row, i) => row.concat(r[i]));
  for (let c = 0; c < n; c++) {
    let p = c; for (let k = c + 1; k < n; k++) if (Math.abs(a[k][c]) > Math.abs(a[p][c])) p = k;
    [a[c], a[p]] = [a[p], a[c]];
    for (let j = c + 1; j <= n; j++) a[c][j] /= a[c][c]; a[c][c] = 1;
    for (let k = 0; k < n; k++) if (k !== c) { const f = a[k][c]; for (let j = c; j <= n; j++) a[k][j] -= f * a[c][j]; }
  }
  return a.map(row => row[n]);
}
function invert3(m) {
  const [[a, b, c], [d, e, f], [g, h, i]] = m, A = e * i - f * h, B = -(d * i - f * g), C = d * h - e * g;
  const det = a * A + b * B + c * C;
  return [[A / det, -(b * i - c * h) / det, (b * f - c * e) / det], [B / det, (a * i - c * g) / det, -(a * f - c * d) / det], [C / det, -(a * h - b * g) / det, (a * e - b * d) / det]];
}

// --- 5. Çalıştır ve ölç ------------------------------------------------------------------------
const rows = [];
for (const s of scenarios) {
  seed = 42;
  const { image, truth } = s.build();
  const runs = [];
  let scene;
  for (let k = 0; k < 3; k++) { const t0 = performance.now(); scene = Vision.analyze(image, { widthMm: WIDTH_MM, heightMm: HEIGHT_MM, threshold: 45, minAreaMm2: 60 }); runs.push(performance.now() - t0); }
  let inter = 0, union = 0, truthArea = 0, predArea = 0;
  for (let i = 0; i < truth.length; i++) {
    const t = truth[i], p = scene.binary[i] ? 1 : 0;
    if (t && p) inter++; if (t || p) union++; truthArea += t; predArea += p;
  }
  const iou = union ? inter / union : 1;
  const areaErrPct = (predArea - truthArea) / truthArea * 100;
  const ok = iou >= 0.95 && scene.components.length === s.parts;
  if (exportDir) {
    const id = String(rows.length + 1).padStart(2, '0');
    writePPM(path.join(exportDir, id + '_goruntu.ppm'), image);
    writePGM(path.join(exportDir, id + '_dogru_maske.pgm'), truth, W, H);
    writePGM(path.join(exportDir, id + '_reform_maske.pgm'), scene.binary, W, H);
  }
  rows.push({ ...s, found: scene.components.length, iou, areaErrPct, ms: runs.sort((a, b) => a - b)[1], ok,
              warn: diagnostics(scene) });
}
const persp = perspectiveTest();

// Uygulamadaki fotoğraf uyarılarının aynısı (production.diagnostics) — kullanıcı uyarıldı mı?
function diagnostics(scene) {
  const w = [];
  if (!scene.components.length) w.push('sınır yok');
  if (scene.coverage > .95) w.push('zemin az');
  const e = (scene.edgeBandMm || 0) + 1;
  if (scene.components.some(c => c.bbox.x < e || c.bbox.y < e || c.bbox.x + c.bbox.width > scene.widthMm - e || c.bbox.y + c.bbox.height > scene.heightMm - e)) w.push('kenara değiyor');
  const tiny = scene.components.filter(c => c.areaMm2 < 400).length;
  if (scene.components.length > 12 && tiny > 8) w.push('çok parça');
  if (scene.components.some(c => c.bbox.width > scene.widthMm * 0.9 && c.bbox.height > scene.heightMm * 0.9 && c.areaMm2 < c.bbox.width * c.bbox.height * 0.6)) w.push('zemin deseni');
  return w;
}

// --- 6. Rapor ----------------------------------------------------------------------------------
const f1 = n => n.toFixed(1).replace('.', ','), f3 = n => n.toFixed(3).replace('.', ',');
const passed = rows.filter(r => r.ok).length;
const lines = [];
lines.push('# ReForm — Görüntü işleme test sonuçları', '');
lines.push(`Tarih: ${new Date().toISOString().slice(0, 10)} · Node ${process.version} · Test edilen dosya: ${path.basename(htmlPath)}`, '');
lines.push(`Görüntü: ${W} × ${H} piksel = ${WIDTH_MM} × ${HEIGHT_MM} mm (${PX_PER_MM} piksel/mm). Eşik 45, en küçük parça 60 mm² (uygulamadaki varsayılanlar).`, '');
lines.push(`**Sonuç: ${passed} / ${rows.length} senaryo başarılı** (ölçüt: IoU ≥ 0,95 ve parça sayısı doğru).`, '');
lines.push('| # | Senaryo | Grup | Beklenen / bulunan parça | IoU | Alan hatası | Süre (ms) | Uygulama uyarısı | Sonuç |');
lines.push('|---|---|---|---|---|---|---|---|---|');
rows.forEach((r, i) => lines.push(`| ${i + 1} | ${r.name} | ${r.group} | ${r.parts} / ${r.found} | ${f3(r.iou)} | %${f1(r.areaErrPct)} | ${Math.round(r.ms)} | ${r.warn.join(', ') || '—'} | ${r.ok ? '✓' : '✗'} |`));
lines.push('', '## Eğik çekim (perspektif düzeltme) testi', '');
lines.push('Fotoğraf yamuk açıyla çekilmiş gibi üretildi; 4 köşe verilip düzeltildi. Gerçek parça 150 × 100 mm.', '');
lines.push('| Bulunan parça | En hatası | Boy hatası | Alan hatası | Süre (ms) |', '|---|---|---|---|---|');
lines.push(`| ${persp.found} | ${f1(persp.widthErr)} mm | ${f1(persp.heightErr)} mm | %${f1(persp.areaErrPct)} | ${Math.round(persp.ms)} |`);
const failed = rows.filter(r => !r.ok);
if (failed.length) {
  lines.push('', '## Başarısız senaryolar ve nedenleri', '');
  const why = {
    'Çok düşük kontrast: beyaz zemin, beyaz karton': 'Malzeme ile zemin arasındaki renk farkı eşiğin altında kalıyor; yöntem yalnızca renk farkına bakıyor. Otomatik modda uygulama bu durumda YZ modeline geçiyor.',
    'Açık zeminde gölge (parçanın sağında)': 'Gri gölge, açık zeminden eşikten daha fazla farklı olduğu için malzemeye ekleniyor; parça olduğundan büyük ölçülüyor. Çözüm: dağınık/tepeden ışık veya koyu zemin.',
    'Birbirine değen iki parça': 'Değen parçalar tek bağlı bölge olarak birleşiyor. Çözüm: parçaları birkaç mm aralıklı koymak.',
    'Desenli zemin (32 px ≈ 11 mm kareli, kesim matı gibi)': 'Zemin tek renk varsayımı bozuluyor; desen kareleri malzeme sanılıyor. Uygulama "çok parça" uyarısı veriyor ve otomatik modda YZ modeline geçiyor.',
    'Kesim matı (yeşil zemin, 10 mm çizgiler)': 'Çizgiler birbirine bağlı bir ağ oluşturuyor ve parçayla birleşip alanın tamamını kaplıyor. Uygulama "zemin deseni" uyarısı veriyor ve otomatik modda YZ modeline geçiyor.',
    'Desenli zeminde delikli parça': 'Desenli zemin hem parçanın çevresinde hem deliğin içinde malzeme sanılıyor. Hibrit yöntem (YZ) bu durumu çözüyor; bkz. HIBRIT_TEST_SONUCLARI.md.',
    'Kenara değen parça (kadraj dışına taşıyor)': 'Parçanın bir kısmı kadraj dışında; ölçülen alan doğru ama parça eksik. Uygulama "kenara değiyor" uyarısı veriyor.',
  };
  failed.forEach(r => lines.push(`- **${r.name}** — IoU ${f3(r.iou)}, parça ${r.parts}/${r.found}. ${why[r.name] || ''}`));
}
lines.push('', '> Not: Bunlar yapay görüntülerdir ve yöntemin sınırlarını kontrollü biçimde gösterir. Gerçek fotoğraf sonuçları için README’deki "Gerçek fotoğraf testi" tablosunu doldurun.');
const md = lines.join('\n') + '\n';
console.log(md);
if (mdPath) { fs.writeFileSync(mdPath, md, 'utf8'); console.log('Yazıldı: ' + mdPath); }
if (exportDir) {
  const summary = rows.map((r, i) => ({ id: String(i + 1).padStart(2, '0'), name: r.name, parts: r.parts, found: r.found, iou: r.iou, ms: r.ms }));
  fs.writeFileSync(path.join(exportDir, 'reform_sonuclar.json'), JSON.stringify(summary, null, 2), 'utf8');
  console.log('Senaryolar dışa aktarıldı: ' + exportDir);
}
