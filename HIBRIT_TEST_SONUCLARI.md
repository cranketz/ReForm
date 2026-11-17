# ReForm — Hibrit (klasik + YZ) test sonuçları

Uygulamanın kendisi (ReForm_MVP.html) Chrome içinde çalıştırıldı; YZ modeli uygulamaya gömülü U²-Net (u2netp) ve onnxruntime-web.
Görüntü 900 × 600 px = 300 × 200 mm (3 px/mm). Ölçüt: IoU ≥ 0,95 ve parça sayısı doğru. YZ modelinin ilk yüklenmesi: 2900 ms (yalnız bir kez).

Hücrelerde: sonuç · IoU · bulunan parça · süre (ms).

| # | Senaryo | Beklenen parça | Yalnız klasik | Otomatik (hibrit) | Her zaman YZ | Otomatik modda kullanılan yöntem |
|---|---|---|---|---|---|---|
| 1 | İdeal: koyu düz zemin, açık ahşap | 1 | ✓ 1,000 · 1 · 56 | ✓ 1,000 · 1 · 38 | ✓ 0,996 · 1 · 1971 | Klasik |
| 2 | Düşük kontrast: bej zemin, açık ahşap | 1 | ✓ 1,000 · 1 · 23 | ✓ 1,000 · 1 · 21 | ✓ 1,000 · 1 · 1982 | Klasik |
| 3 | Çok düşük kontrast: beyaz zemin, beyaz karton | 1 | ✗ 0,000 · 0 · 16 | ✓ 1,000 · 1 · 1777 | ✓ 1,000 · 1 · 1907 | Hibrit: YZ (U²-Net) |
| 4 | Işık eğimi: sol kenar %45 karanlık | 1 | ✓ 1,000 · 1 · 47 | ✓ 1,000 · 1 · 73 | ✓ 0,996 · 1 · 1883 | Klasik |
| 5 | Koyu zeminde gölge (parçanın sağında) | 1 | ✓ 1,000 · 1 · 87 | ✓ 1,000 · 1 · 23 | ✗ 0,933 · 1 · 1899 | Klasik |
| 6 | Açık zeminde gölge (parçanın sağında) | 1 | ✗ 0,938 · 1 · 26 | ✗ 0,938 · 1 · 24 | ✗ 0,936 · 1 · 1799 | Klasik |
| 7 | Güçlü gürültü (±40) | 1 | ✓ 1,000 · 1 · 61 | ✓ 1,000 · 1 · 78 | ✓ 0,998 · 1 · 1864 | Klasik |
| 8 | Bulanıklık (7 × 7 piksel ortalama) | 1 | ✓ 0,978 · 1 · 26 | ✓ 0,978 · 1 · 24 | ✓ 0,984 · 1 · 1847 | Klasik |
| 9 | Ahşap dokusu (damarlı yüzey) | 1 | ✓ 1,000 · 1 · 25 | ✓ 1,000 · 1 · 26 | ✓ 0,995 · 1 · 1851 | Klasik |
| 10 | Delikli parça (ortada 40 mm delik) | 1 | ✓ 1,000 · 1 · 38 | ✓ 1,000 · 1 · 39 | ✓ 0,997 · 1 · 1928 | Klasik |
| 11 | İki ayrı parça | 2 | ✓ 1,000 · 2 · 26 | ✓ 1,000 · 2 · 28 | ✓ 0,995 · 2 · 1976 | Klasik |
| 12 | Birbirine değen iki parça | 2 | ✗ 1,000 · 1 · 25 | ✗ 1,000 · 1 · 26 | ✗ 0,995 · 1 · 1754 | Klasik |
| 13 | Desenli zemin (32 px ≈ 11 mm kareli, kesim matı gibi) | 1 | ✗ 0,432 · 170 · 99 | ✓ 0,994 · 1 · 1808 | ✓ 0,994 · 1 · 1871 | Hibrit: YZ (U²-Net) |
| 14 | Kesim matı (yeşil zemin, 10 mm çizgiler) | 1 | ✗ 0,743 · 1 · 54 | ✓ 0,993 · 1 · 1829 | ✓ 0,993 · 1 · 1802 | Hibrit: YZ (U²-Net) |
| 15 | Desenli zeminde delikli parça | 1 | ✗ 0,395 · 173 · 51 | ✓ 0,960 · 1 · 1719 | ✓ 0,960 · 1 · 1740 | Hibrit: YZ (U²-Net) |
| 16 | Masa kenarı görünüyor (köşeler ~2 mm dışarıdan seçilmiş) | 1 | ✓ 1,000 · 1 · 22 | ✓ 1,000 · 1 · 23 | ✓ 0,996 · 1 · 1879 | Klasik |
| 17 | Kenara değen parça (kadraj dışına taşıyor) | 1 | ✓ 0,953 · 1 · 21 | ✓ 0,953 · 1 · 21 | ✗ 0,950 · 1 · 1941 | Klasik |

| Mod | Başarılı senaryo | Ortalama IoU | Ortanca süre (ms) | YZ kullanılan senaryo |
|---|---|---|---|---|
| Yalnız klasik | 11 / 17 | 0,849 | 26 | 0 |
| Otomatik (hibrit) | 15 / 17 | 0,989 | 28 | 4 |
| Her zaman YZ | 13 / 17 | 0,983 | 1879 | 17 |

## Yorum

- **Otomatik (hibrit) mod en iyisi:** 17 senaryonun 15'inde başarılı, ortalama IoU 0,989. Yalnız klasik yöntem 11/17, her zaman YZ 13/17.
- **Hız korunuyor:** YZ yalnız 4 senaryoda, klasik yöntemin zorlandığı durumlarda çalıştı. Ortanca süre klasik yöntemle hemen hemen aynı (~25–30 ms). YZ çalıştığında süre ~2 saniye; model ilk kez yüklenirken bir kez daha ~1–3 saniye.
- **YZ'nin çözdüğü durumlar:** Beyaz zeminde beyaz karton, kareli zemin, kesim matı (çizgiler parçayla birleşip alanı kaplıyor) ve desenli zeminde delikli parça.
- **İki yöntemin de çözemediği durumlar:**
  1. *Açık zeminde gölge:* Gölge malzemeye ekleniyor, alan %6–7 fazla çıkıyor. Klasik yöntem bu durumu "şüpheli" saymadığı için YZ'ye geçilmiyor; YZ de gölgeyi nesneye katıyor.
  2. *Birbirine değen iki parça:* Tek parça sayılıyor. Parçalar arasında birkaç mm boşluk bırakılmalı.
- **Kenar şeridi:** Görüntünün en dış ~4,5 mm'lik şeridi yok sayılıyor (köşe seçme hatalarına karşı). Bu yüzden kadraj dışına taşan parça bu şerit kadar küçük ölçülüyor (senaryo 17, IoU 0,953).
- **YZ maskesinin kenar payı:** YZ maskesi kenarlarda ~1–2 mm taşabiliyor. YZ kullanıldığında uygulama "parça sınırlarını görselde kontrol et" uyarısı veriyor.
- **Gerçekçi fotoğraflarla doğrulama:** `test_fotograflari/CEVAP_ANAHTARI.md` dosyasındaki 10 fotoğrafta otomatik mod 8/10 doğru; doğru olanlarda ölçü hatası en fazla 1,7 mm.
