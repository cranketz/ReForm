# ReForm — Test fotoğrafları ve cevap anahtarı

Bu klasördeki 10 fotoğraf **bilgisayarda üretildi**: gerçek fotoğrafa benzesin diye eğik açı, ahşap / MDF / keçe dokusu, gölge, ışık farkı, kenar kararması, sensör gürültüsü, hafif bulanıklık ve JPEG sıkıştırması eklendi. Her parçanın gerçek ölçüsü bilindiği için uygulamanın hatası mm olarak hesaplanabiliyor.

> Jüri gerçek girdi istiyor (rubrik 4.1). Bu fotoğraflar test ve prova içindir; sunumda en az birkaç **kendi çektiğin** fotoğrafı da göster. Çekim önerileri en altta.

## Nasıl kullanılır

1. `ReForm_MVP.html` dosyasını aç → **Fotoğraf yükle** → bir test fotoğrafı seç.
2. Alan ölçüsü **30 × 20 cm** olmalı (varsayılan). Bütün fotoğraflarda parçalar 300 × 200 mm'lik bir pano / kağıt / kesim matı üzerinde.
3. Panonun 4 köşesine **sol üst → sağ üst → sağ alt → sol alt** sırasıyla tıkla → **Ölçüyü uygula**. Köşeleri birkaç mm şaşırman sorun değil.
4. Ölçüyü **Kesim 3D** sekmesinde (En / Boy) ve alttaki durum satırında (parça sayısı, kullanılan yöntem, süre) gör.
5. Ayırma yöntemini değiştirmek için: **Boyutları düzenle → Gelişmiş ayarlar → Malzemeyi ayırma yöntemi**.

## Cevap anahtarı

"Gerçek" sütunu parçaların gerçek ölçüsü (birden fazla parça varsa hepsini çevreleyen dikdörtgen). "Uygulama" sütunu, uygulamanın **Otomatik** modda bu fotoğraflarla verdiği sonuç (köşeler tam yerinden seçilerek, 17 Kasım 2026).

| # | Fotoğraf | Ne test ediyor | Gerçek | Uygulama (Otomatik) | Hata (en / boy) | Yalnız klasik | Sonuç |
|---|---|---|---|---|---|---|---|
| 1 | `01_kolay_koyu_zemin.jpg` | Koyu zemin, L biçimli kontrplak, hafif açı | 1 parça · 140 × 110 mm | 1 parça · 141,3 × 110,7 mm · Klasik | +1,3 / +0,7 mm | 1 parça · 141,3 × 110,7 mm | ✓ |
| 2 | `02_egik_cekim.jpg` | Güçlü eğik açıdan çekim (perspektif) | 1 parça · 173 × 126 mm | 1 parça · 174,0 × 126,7 mm · Klasik | +1,0 / +0,7 mm | 1 parça · 174,0 × 126,7 mm | ✓ |
| 3 | `03_iki_mdf_yan_isik.jpg` | İki ayrı MDF parça, yandan gelen ışık | 2 parça · 240 × 130 mm | 2 parça · 241,3 × 130,3 mm · Klasik | +1,3 / +0,3 mm | 2 parça · 241,3 × 130,3 mm | ✓ |
| 4 | `04_delikli_parca.jpg` | Kontrplakta yuvarlak ve dikdörtgen delik | 1 parça · 220 × 140 mm | 1 parça · 221,7 × 141,0 mm · Klasik | +1,7 / +1,0 mm | 1 parça · 221,7 × 141,0 mm | ✓ (delikler korunuyor) |
| 5 | `05_beyaz_zemin_beyaz_karton.jpg` | Beyaz kağıt üzerinde beyaz karton | 1 parça · 180 × 125 mm | 1 parça · 181,7 × 125,3 mm · Hibrit: YZ (U²-Net) | +1,7 / +0,3 mm | 0 parça | ✓ YZ devreye giriyor |
| 6 | `06_kesim_mati.jpg` | Yeşil kareli kesim matı üzerinde kontrplak | 1 parça · 140 × 100 mm | 1 parça · 141,7 × 101,7 mm · Hibrit: YZ (U²-Net) | +1,7 / +1,7 mm | 1 parça · 290,7 × 190,7 mm | ✓ YZ devreye giriyor |
| 7 | `07_acik_zemin_golge.jpg` | Açık gri zemin, sert gölge | 1 parça · 140 × 100 mm | 1 parça · 149,7 × 107,7 mm · Klasik | +9,7 / +7,7 mm | 1 parça · 149,7 × 107,7 mm | ✗ beklenen hata: gölge parçaya ekleniyor |
| 8 | `08_degen_parcalar.jpg` | Birbirine değen iki kontrplak parça | 2 parça · 220 × 120 mm | 1 parça · 221,7 × 121,0 mm · Klasik | +1,7 / +1,0 mm | 1 parça · 221,7 × 121,0 mm | ✗ beklenen hata: değen parçalar tek parça |
| 9 | `09_kece_duzensiz.jpg` | Kırmızı keçe, düzensiz kenar, hafif bulanık | 1 parça · 166 × 97 mm | 1 parça · 167,0 × 97,7 mm · Klasik | +1,0 / +0,7 mm | 1 parça · 167,0 × 97,7 mm | ✓ |
| 10 | `10_kucuk_artiklar.jpg` | Altı küçük kontrplak artığı (biri 6 × 6 mm) | 5 (+1 küçük) parça · 241,0 × 154,0 mm* | 5 parça · 241,3 × 154,3 mm · Klasik | +0,3 / +0,3 mm | 5 parça · 241,3 × 154,3 mm | ✓ 6 × 6 mm'lik parça bilerek atılıyor |

\* 10. fotoğrafta 6 × 6 mm'lik (36 mm²) parça, en küçük parça sınırı olan 60 mm²'nin altında kaldığı için bilerek atılıyor; genel ölçü bu parça hariç verildi.

### Parça parça gerçek ölçüler

| # | Parça | En × boy (mm) | Alan (mm²) | Delik |
|---|---|---|---|---|
| 1 | L kontrplak | 140 × 110 | 10525 | — |
| 2 | Kontrplak levha | 173 × 126 | 16824 | — |
| 3 | MDF A | 110 × 120 | 13200 | — |
| 3 | MDF B | 100 × 130 | 10188 | — |
| 4 | Delikli kontrplak | 220 × 140 | 26602 | Ø50 mm daire + 55 × 40 mm dikdörtgen |
| 5 | Beyaz karton | 180 × 125 | 18434 | — |
| 6 | Kontrplak | 140 × 100 | 14000 | — |
| 7 | MDF | 140 × 100 | 14000 | — |
| 8 | Kontrplak A | 110 × 120 | 13200 | — |
| 8 | Kontrplak B (A’ya değiyor) | 110 × 80 | 8800 | — |
| 9 | Kırmızı keçe | 166 × 97 | 10986 | — |
| 10 | Artık 1 | 60 × 45 | 2700 | — |
| 10 | Artık 2 | 35 × 70 | 2450 | — |
| 10 | Artık 3 | 96 × 58 | 3603 | — |
| 10 | Artık 4 | 80 × 55 | 4400 | — |
| 10 | Artık 5 | 115 × 65 | 5608 | — |
| 10 | Artık 6 | 6 × 6 | 36 | — |

## Sonuçların özeti

- **Otomatik modda 10 fotoğrafın 8'i doğru**; kalan 2'si bilerek konan zor durumlar (açık zeminde gölge, birbirine değen parçalar).
- Doğru bulunan fotoğraflarda **ölçü hatası en fazla ~1,7 mm**; uygulama parçaları çoğunlukla 1–1,5 mm büyük ölçüyor (yumuşak kenarlar ve parçanın hemen yanındaki gölge).
- **YZ yalnız gereken 2 fotoğrafta** (beyaz zeminde beyaz karton, kesim matı) devreye girdi; bu ikisinde yalnız klasik yöntem ya hiç parça bulamıyor ya da matın tamamını parça sanıyor.
- Gölgeli fotoğrafta parça 140 × 100 mm iken ~150 × 108 mm ölçülüyor: sunumda "başarısız örnek ve nedeni" olarak kullanılabilir (rubrik 5.3).

## Kendi fotoğraflarını çekerken

- Parçaları **ölçüsünü bildiğin düz bir zeminin** üzerine koy: A4 kağıt (297 × 210 mm), karton ya da pano. Uygulamada alan ölçüsünü buna göre seç (Alan ölçüsü → Özel ölçü).
- Zemin malzemeden **farklı renkte** olsun (açık ahşap için koyu zemin). Aynı renkse YZ devreye girer ama ~2 sn sürer.
- Zeminin **4 köşesi de** kadrajda görünsün; parçalar birbirine ve zeminin kenarına değmesin.
- Işık tepeden ve dağınık gelsin (pencere ışığı, tavan lambası); sert yan ışık gölge yapar.
- Telefonu olabildiğince **tepeden** tut; eğik açı da olur, ama köşeleri dikkatli seç.
- Her parçanın enini ve boyunu cetvelle ölç, README'deki "Gerçek fotoğraf testi" tablosuna yaz.
