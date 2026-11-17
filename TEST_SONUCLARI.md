# ReForm — Görüntü işleme test sonuçları

Tarih: 2026-11-17 · Node v22.23.4 · Test edilen dosya: ReForm_MVP.html

Görüntü: 900 × 600 piksel = 300 × 200 mm (3 piksel/mm). Eşik 45, en küçük parça 60 mm² (uygulamadaki varsayılanlar).

**Sonuç: 11 / 17 senaryo başarılı** (ölçüt: IoU ≥ 0,95 ve parça sayısı doğru).

| # | Senaryo | Grup | Beklenen / bulunan parça | IoU | Alan hatası | Süre (ms) | Uygulama uyarısı | Sonuç |
|---|---|---|---|---|---|---|---|---|
| 1 | İdeal: koyu düz zemin, açık ahşap | temel | 1 / 1 | 1,000 | %0,0 | 193 | — | ✓ |
| 2 | Düşük kontrast: bej zemin, açık ahşap | renk | 1 / 1 | 1,000 | %0,0 | 153 | — | ✓ |
| 3 | Çok düşük kontrast: beyaz zemin, beyaz karton | renk | 1 / 0 | 0,000 | %-100,0 | 52 | sınır yok | ✗ |
| 4 | Işık eğimi: sol kenar %45 karanlık | ışık | 1 / 1 | 1,000 | %0,0 | 167 | — | ✓ |
| 5 | Koyu zeminde gölge (parçanın sağında) | ışık | 1 / 1 | 1,000 | %0,0 | 141 | — | ✓ |
| 6 | Açık zeminde gölge (parçanın sağında) | ışık | 1 / 1 | 0,938 | %6,6 | 115 | — | ✗ |
| 7 | Güçlü gürültü (±40) | kalite | 1 / 1 | 1,000 | %0,0 | 179 | — | ✓ |
| 8 | Bulanıklık (7 × 7 piksel ortalama) | kalite | 1 / 1 | 0,978 | %2,2 | 140 | — | ✓ |
| 9 | Ahşap dokusu (damarlı yüzey) | kalite | 1 / 1 | 1,000 | %0,0 | 139 | — | ✓ |
| 10 | Delikli parça (ortada 40 mm delik) | şekil | 1 / 1 | 1,000 | %0,0 | 129 | — | ✓ |
| 11 | İki ayrı parça | şekil | 2 / 2 | 1,000 | %0,0 | 200 | — | ✓ |
| 12 | Birbirine değen iki parça | şekil | 2 / 1 | 1,000 | %0,0 | 149 | — | ✗ |
| 13 | Desenli zemin (32 px ≈ 11 mm kareli, kesim matı gibi) | zemin | 1 / 170 | 0,432 | %131,3 | 314 | kenara değiyor, çok parça | ✗ |
| 14 | Kesim matı (yeşil zemin, 10 mm çizgiler) | zemin | 1 / 1 | 0,743 | %34,6 | 237 | kenara değiyor, zemin deseni | ✗ |
| 15 | Desenli zeminde delikli parça | zemin | 1 / 173 | 0,395 | %152,9 | 315 | kenara değiyor, çok parça | ✗ |
| 16 | Masa kenarı görünüyor (köşeler ~2 mm dışarıdan seçilmiş) | kadraj | 1 / 1 | 1,000 | %0,0 | 139 | — | ✓ |
| 17 | Kenara değen parça (kadraj dışına taşıyor) | kadraj | 1 / 1 | 0,953 | %-4,7 | 108 | kenara değiyor | ✓ |

## Eğik çekim (perspektif düzeltme) testi

Fotoğraf yamuk açıyla çekilmiş gibi üretildi; 4 köşe verilip düzeltildi. Gerçek parça 150 × 100 mm.

| Bulunan parça | En hatası | Boy hatası | Alan hatası | Süre (ms) |
|---|---|---|---|---|
| 1 | 0,7 mm | 0,7 mm | %0,3 | 534 |

## Başarısız senaryolar ve nedenleri

- **Çok düşük kontrast: beyaz zemin, beyaz karton** — IoU 0,000, parça 1/0. Malzeme ile zemin arasındaki renk farkı eşiğin altında kalıyor; yöntem yalnızca renk farkına bakıyor. Otomatik modda uygulama bu durumda YZ modeline geçiyor.
- **Açık zeminde gölge (parçanın sağında)** — IoU 0,938, parça 1/1. Gri gölge, açık zeminden eşikten daha fazla farklı olduğu için malzemeye ekleniyor; parça olduğundan büyük ölçülüyor. Çözüm: dağınık/tepeden ışık veya koyu zemin.
- **Birbirine değen iki parça** — IoU 1,000, parça 2/1. Değen parçalar tek bağlı bölge olarak birleşiyor. Çözüm: parçaları birkaç mm aralıklı koymak.
- **Desenli zemin (32 px ≈ 11 mm kareli, kesim matı gibi)** — IoU 0,432, parça 1/170. Zemin tek renk varsayımı bozuluyor; desen kareleri malzeme sanılıyor. Uygulama "çok parça" uyarısı veriyor ve otomatik modda YZ modeline geçiyor.
- **Kesim matı (yeşil zemin, 10 mm çizgiler)** — IoU 0,743, parça 1/1. Çizgiler birbirine bağlı bir ağ oluşturuyor ve parçayla birleşip alanın tamamını kaplıyor. Uygulama "zemin deseni" uyarısı veriyor ve otomatik modda YZ modeline geçiyor.
- **Desenli zeminde delikli parça** — IoU 0,395, parça 1/173. Desenli zemin hem parçanın çevresinde hem deliğin içinde malzeme sanılıyor. Hibrit yöntem (YZ) bu durumu çözüyor; bkz. HIBRIT_TEST_SONUCLARI.md.

> Not: Bunlar yapay görüntülerdir ve yöntemin sınırlarını kontrollü biçimde gösterir. Gerçek fotoğraf sonuçları için README’deki "Gerçek fotoğraf testi" tablosunu doldurun.
