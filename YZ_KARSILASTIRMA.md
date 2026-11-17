# ReForm — Klasik yöntem ile YZ modeli karşılaştırması

Aynı yapay test görüntüleri (900 × 600 px, 3 px/mm). Ölçüt: IoU ≥ 0,95 ve parça sayısı doğru.

Hücrelerde: IoU · bulunan parça · süre (ms).

| # | Senaryo | Beklenen parça | ReForm | u2netp | u2net |
|---|---|---|---|---|---|
| 1 | İdeal: koyu düz zemin, açık ahşap | 1 | ✓ 1,000 · 1 · 193 | ✓ 0,997 · 1 · 533 | ✓ 0,993 · 1 · 1154 |
| 2 | Düşük kontrast: bej zemin, açık ahşap | 1 | ✓ 1,000 · 1 · 153 | ✓ 1,000 · 1 · 441 | ✓ 0,997 · 1 · 1025 |
| 3 | Çok düşük kontrast: beyaz zemin, beyaz karton | 1 | ✗ 0,000 · 0 · 52 | ✓ 1,000 · 1 · 515 | ✓ 0,997 · 1 · 1026 |
| 4 | Işık eğimi: sol kenar %45 karanlık | 1 | ✓ 1,000 · 1 · 167 | ✓ 0,997 · 1 · 422 | ✓ 0,995 · 1 · 956 |
| 5 | Koyu zeminde gölge (parçanın sağında) | 1 | ✓ 1,000 · 1 · 141 | ✗ 0,934 · 1 · 432 | ✗ 0,936 · 1 · 988 |
| 6 | Açık zeminde gölge (parçanın sağında) | 1 | ✗ 0,938 · 1 · 115 | ✗ 0,936 · 1 · 433 | ✗ 0,932 · 1 · 964 |
| 7 | Güçlü gürültü (±40) | 1 | ✓ 1,000 · 1 · 179 | ✓ 0,999 · 1 · 422 | ✓ 0,987 · 1 · 956 |
| 8 | Bulanıklık (7 × 7 piksel ortalama) | 1 | ✓ 0,978 · 1 · 140 | ✓ 0,984 · 1 · 420 | ✓ 0,984 · 1 · 1000 |
| 9 | Ahşap dokusu (damarlı yüzey) | 1 | ✓ 1,000 · 1 · 139 | ✓ 0,995 · 1 · 429 | ✓ 0,993 · 1 · 980 |
| 10 | Delikli parça (ortada 40 mm delik) | 1 | ✓ 1,000 · 1 · 129 | ✗ 0,891 · 1 · 418 | ✗ 0,893 · 1 · 1055 |
| 11 | İki ayrı parça | 2 | ✓ 1,000 · 2 · 200 | ✓ 0,994 · 2 · 429 | ✓ 0,989 · 2 · 983 |
| 12 | Birbirine değen iki parça | 2 | ✗ 1,000 · 1 · 149 | ✗ 0,994 · 1 · 432 | ✗ 0,994 · 1 · 1002 |
| 13 | Desenli zemin (32 px ≈ 11 mm kareli, kesim matı gibi) | 1 | ✗ 0,432 · 170 · 314 | ✓ 0,993 · 1 · 420 | ✓ 0,995 · 1 · 1008 |
| 14 | Kesim matı (yeşil zemin, 10 mm çizgiler) | 1 | ✗ 0,743 · 1 · 237 | ✓ 0,993 · 1 · 426 | ✓ 0,993 · 1 · 954 |
| 15 | Desenli zeminde delikli parça | 1 | ✗ 0,395 · 173 · 315 | ✗ 0,967 · 2 · 428 | ✗ 0,892 · 1 · 959 |
| 16 | Masa kenarı görünüyor (köşeler ~2 mm dışarıdan seçilmiş) | 1 | ✓ 1,000 · 1 · 139 | ✓ 0,997 · 1 · 416 | ✓ 0,996 · 1 · 977 |
| 17 | Kenara değen parça (kadraj dışına taşıyor) | 1 | ✓ 0,953 · 1 · 108 | ✓ 0,996 · 1 · 411 | ✓ 0,993 · 1 · 994 |

| Yöntem | Başarılı senaryo | Ortalama IoU | Ortanca süre (ms) | Model boyutu | Çevrim dışı | Ölçek (mm) |
|---|---|---|---|---|---|---|
| ReForm | 11 / 17 | 0,849 | 149 | 0 (kod ~40 KB) | evet, tarayıcıda | evet, 4 köşe ile |
| u2netp | 12 / 17 | 0,980 | 428 | 4,6 MB | evet (indirildikten sonra), Python gerekir | hayır, yalnız maske verir |
| u2net | 12 / 17 | 0,974 | 988 | 176 MB | evet (indirildikten sonra), Python gerekir | hayır, yalnız maske verir |

## Yorum

- **Hazır modeller tek başına yeterli değil.** Klasik yöntem 11/17, hazır U²-Net modelleri 12/17 başarılı; farklı yerlerde başarısız oluyorlar.
- **YZ modelinin üstün olduğu yer:** Düşük kontrast (beyaz zeminde beyaz karton), desenli zemin ve kesim matı. Model "nesne" kavramını öğrendiği için yalnız renge bakmıyor.
- **Klasik yöntemin üstün olduğu yer:** Delikli parça (U²-Net deliği kapatıyor, IoU 0,89) ve koyu zemindeki gölge. ReForm için delik kritik: delik kapanırsa ürün parçası deliğin üstüne yerleşir ve hatalı kesilir.
- **Ölçek:** Hiçbir model mm ölçeği vermiyor; perspektif düzeltme ve mm dönüşümü her durumda gerekiyor.
- **Karar → hibrit yöntem:** Bu karşılaştırmaya dayanarak uygulamaya hibrit yöntem eklendi. Klasik yöntem şüpheli sonuç verdiğinde küçük U²-Net modeli devreye giriyor, delikler klasik maskeden geri alınıyor. Sonuç: **17 senaryonun 15'inde başarılı, ortalama IoU 0,989**. Ayrıntılar: [`HIBRIT_TEST_SONUCLARI.md`](HIBRIT_TEST_SONUCLARI.md).

> Bu tablodaki süreler Python'da (rembg, CPU) ve Node.js'te ölçüldü. Uygulamanın içindeki tarayıcı süreleri HIBRIT_TEST_SONUCLARI.md dosyasında.
