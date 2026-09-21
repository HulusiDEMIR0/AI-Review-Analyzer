import json
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


# ============================================================
# AYARLAR
# ============================================================

OUTPUT_DIR = Path("./v5")

SECTIONS = [
    "TEMEL ÖZELLİKLER",
    "EKRAN",
    "BATARYA",
    "KAMERA",
    "TEMEL DONANIM",
    "TASARIM",
    "AĞ BAĞLANTILARI",
    "İŞLETİM SİSTEMİ",
    "KABLOSUZ BAĞLANTILAR",
    "ÇOKLU ORTAM",
    "ÖZELLİKLER",
    "DİĞER BAĞLANTILAR",
    "AB ÜRÜN KAYIT ve ENERJİ ETİKETİ",
    "TEMEL BİLGİLER",
]


# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================

def temizle(metin):
    return re.sub(
        r"[ \u00a0]+",
        " ",
        metin
    ).strip()


def dosya_adi(metin):
    metin = metin.lower()
    metin = re.sub(r"[^a-z0-9çğıöşü]+", "_", metin, flags=re.IGNORECASE)
    return metin.strip("_")


def parse_section(lines, start_idx, end_idx):
    """
    Epey'nin karşılaştırma metnindeki bir bölümü okur.

    Yapı kabaca:
        Özellik adı
        Ürün 1 değeri / değerleri
        <TAB>
        Ürün 2 değeri / değerleri

    Çok satırlı değerleri tek bir değere çevirir ve
    satırları tekrar yanlışlıkla özellik adı olarak okumaz.
    """

    rows = {}

    i = start_idx + 1

    while i < end_idx:

        # Boş satırları geç
        if not lines[i].strip():
            i += 1
            continue

        # Özellik adı
        ozellik = temizle(
            lines[i]
        )

        i += 1

        if not ozellik:
            continue

        # ----------------------------------------------------
        # ÜRÜN 1 DEĞERLERİ
        # ----------------------------------------------------

        urun_1 = []
        ayirici_bulundu = False

        while i < end_idx:

            raw = lines[i]

            # Epey, iki ürün sütununu genellikle tab içeren
            # boş bir satırla ayırıyor.
            if (
                raw.strip() == ""
                and "\t" in raw
            ):
                ayirici_bulundu = True
                i += 1
                break

            # Satır tamamen boşsa bu öğe beklediğimiz row yapısı değil.
            if not raw.strip():
                break

            urun_1.append(
                temizle(raw)
            )

            i += 1

        # İki ürünlü bir satır değilse devam et
        if not ayirici_bulundu:
            continue

        # ----------------------------------------------------
        # ÜRÜN 2 DEĞERLERİ
        # ----------------------------------------------------

        urun_2 = []

        while i < end_idx:

            raw = lines[i]

            # Satır sonundaki boşluk satırı
            if not raw.strip():
                i += 1
                break

            urun_2.append(
                temizle(raw)
            )

            i += 1

        urun_1 = [
            x for x in urun_1
            if x
        ]

        urun_2 = [
            x for x in urun_2
            if x
        ]

        rows[ozellik] = {
            "urun_1": "\n".join(urun_1),
            "urun_2": "\n".join(urun_2),
        }

    return rows


def ozellikleri_ayikla(ham_metin):

    lines = ham_metin.splitlines()

    # --------------------------------------------------------
    # Bölümlerin konumlarını bul
    # --------------------------------------------------------

    positions = []

    for section in SECTIONS:

        bulunanlar = [
            i
            for i, line in enumerate(lines)
            if temizle(line) == section
        ]

        if bulunanlar:
            positions.append(
                (
                    section,
                    bulunanlar[-1]
                )
            )

    # --------------------------------------------------------
    # Her bölümü ayrı ayrı parse et
    # --------------------------------------------------------

    parsed = {}

    for index, (section, start) in enumerate(
        positions
    ):

        if index + 1 < len(positions):

            end = positions[
                index + 1
            ][1]

        else:

            end = len(lines)

        parsed[section] = parse_section(
            lines,
            start,
            end
        )

    return parsed


# ============================================================
# FİYATLARI BUL
# ============================================================

def fiyatlari_bul(ham_metin):

    fiyatlar = re.findall(
        r"\d{1,3}(?:\.\d{3})*,\d{2}\s*TL",
        ham_metin
    )

    # Tekrarları kaldır
    return list(
        dict.fromkeys(fiyatlar)
    )


# ============================================================
# ÜRÜN ADLARINI BUL
# ============================================================

def urun_adlarini_bul(page):

    urunler = []

    # Karşılaştırma sayfasındaki ilk başlıklar
    # içinden olası ürün isimlerini al.
    for selector in [
        "h1",
        "h2",
        "h3"
    ]:

        try:

            metinler = page.locator(
                selector
            ).all_inner_texts()

        except Exception:

            continue

        for metin in metinler:

            metin = temizle(metin)

            if not metin:
                continue

            if "Karşılaştırması" in metin:
                continue

            # Satıcı satırlarını alma
            if metin.startswith("Satıcı:"):
                continue

            # Çok genel başlıkları alma
            if metin.lower() in [
                "telefon",
                "telefon karşılaştırmaları"
            ]:
                continue

            if metin not in urunler:
                urunler.append(metin)

    return urunler


# ============================================================
# EPEY SCRAPER
# ============================================================

def scrape_epey(url):

    baslangic = time.perf_counter()

    with sync_playwright() as p:

        print("\n[1/5] Chromium başlatılıyor...")

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page(
            viewport={
                "width": 1440,
                "height": 900
            }
        )

        try:

            print(
                "\n[2/5] Epey karşılaştırma sayfası açılıyor..."
            )

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
            )

            print(
                "      Sayfa açıldı."
            )

            # Dinamik içeriklerin yüklenmesi
            page.wait_for_timeout(
                5000
            )

            # Sayfanın tamamını yükle
            for _ in range(6):

                page.mouse.wheel(
                    0,
                    5000
                )

                page.wait_for_timeout(
                    1000
                )

            page.evaluate(
                "window.scrollTo(0, 0)"
            )

            page.wait_for_timeout(
                1000
            )


            # ====================================================
            # HAM SAYFA METNİ
            # ====================================================

            print(
                "\n[3/5] Epey verileri okunuyor..."
            )

            ham_metin = page.locator(
                "body"
            ).inner_text()


            # ====================================================
            # VERİLERİ AYIKLA
            # ====================================================

            urunler = urun_adlarini_bul(
                page
            )

            ozellikler = ozellikleri_ayikla(
                ham_metin
            )

            fiyatlar = fiyatlari_bul(
                ham_metin
            )


            # Eğer başlıklardan iki ürün bulunamazsa,
            # sayfadaki standart ürün adlarını metinden yakala.
            if len(urunler) < 2:

                bilinen = []

                for isim in [
                    "Samsung Galaxy S25 FE",
                    "Apple iPhone 17"
                ]:

                    if isim in ham_metin:
                        bilinen.append(isim)

                if len(bilinen) >= 2:
                    urunler = bilinen


            if len(urunler) < 2:

                raise RuntimeError(
                    "Sayfada iki ürün adı bulunamadı."
                )


            if len(fiyatlar) < 2:

                print(
                    "UYARI: İki ayrı fiyat bulunamadı."
                )


            # ====================================================
            # İKİ ÜRÜNÜ AYRI AYRI OLUŞTUR
            # ====================================================

            urun_1 = {
                "kaynak": "Epey",
                "urun_adi": urunler[0],
                "fiyat": (
                    fiyatlar[0]
                    if len(fiyatlar) >= 1
                    else None
                ),
                "karsilastirma_url": url,
                "ozellikler": {}
            }


            urun_2 = {
                "kaynak": "Epey",
                "urun_adi": urunler[1],
                "fiyat": (
                    fiyatlar[1]
                    if len(fiyatlar) >= 2
                    else None
                ),
                "karsilastirma_url": url,
                "ozellikler": {}
            }


            # Her iki ürünün değerlerini ayır
            for section, rows in ozellikler.items():

                urun_1[
                    "ozellikler"
                ][section] = {}

                urun_2[
                    "ozellikler"
                ][section] = {}


                for ozellik, values in rows.items():

                    urun_1[
                        "ozellikler"
                    ][section][ozellik] = values[
                        "urun_1"
                    ]

                    urun_2[
                        "ozellikler"
                    ][section][ozellik] = values[
                        "urun_2"
                    ]


            # ====================================================
            # KARŞILAŞTIRMA JSON
            # ====================================================

            karsilastirma = {
                "kaynak": "Epey",
                "url": url,
                "urunler": [
                    urun_1,
                    urun_2
                ]
            }


            # ====================================================
            # DOSYALARI KAYDET
            # ====================================================

            print(
                "\n[4/5] JSON dosyaları kaydediliyor..."
            )

            OUTPUT_DIR.mkdir(
                parents=True,
                exist_ok=True
            )


            # Ortak karşılaştırma
            karsilastirma_dosyasi = (
                OUTPUT_DIR
                / "epey_karsilastirma.json"
            )


            with karsilastirma_dosyasi.open(
                "w",
                encoding="utf-8"
            ) as dosya:

                json.dump(
                    karsilastirma,
                    dosya,
                    ensure_ascii=False,
                    indent=4
                )


            # Ürün 1
            urun_1_dosyasi = (
                OUTPUT_DIR
                / f"{dosya_adi(urun_1['urun_adi'])}_epey.json"
            )


            with urun_1_dosyasi.open(
                "w",
                encoding="utf-8"
            ) as dosya:

                json.dump(
                    urun_1,
                    dosya,
                    ensure_ascii=False,
                    indent=4
                )


            # Ürün 2
            urun_2_dosyasi = (
                OUTPUT_DIR
                / f"{dosya_adi(urun_2['urun_adi'])}_epey.json"
            )


            with urun_2_dosyasi.open(
                "w",
                encoding="utf-8"
            ) as dosya:

                json.dump(
                    urun_2,
                    dosya,
                    ensure_ascii=False,
                    indent=4
                )


            toplam_sure = (
                time.perf_counter()
                - baslangic
            )


            # ====================================================
            # SONUÇ
            # ====================================================

            print(
                "\n[5/5] Epey scraper tamamlandı."
            )

            print(
                f"      Ürün 1: "
                f"{urun_1['urun_adi']}"
            )

            print(
                f"      Ürün 2: "
                f"{urun_2['urun_adi']}"
            )

            print(
                f"      Özellik bölümü: "
                f"{len(ozellikler)}"
            )

            print(
                f"      Fiyat sayısı: "
                f"{len(fiyatlar)}"
            )

            print(
                f"      Süre: "
                f"{toplam_sure:.2f} saniye"
            )

            print(
                f"\n      Karşılaştırma: "
                f"{karsilastirma_dosyasi}"
            )

            print(
                f"      Ürün 1 JSON: "
                f"{urun_1_dosyasi}"
            )

            print(
                f"      Ürün 2 JSON: "
                f"{urun_2_dosyasi}"
            )

            return karsilastirma

        finally:

            browser.close()


# ============================================================
# PROGRAM
# ============================================================

print("=" * 70)
print("AI REVIEW ANALYZER - V5")
print("EPEY TEKNİK VERİ SCRAPER")
print("=" * 70)


url = input(
    "\nEpey karşılaştırma linkini gir: "
).strip()


if not url:

    print(
        "\nHATA: Link boş bırakılamaz."
    )

    raise SystemExit


try:

    scrape_epey(
        url
    )

except Exception as hata:

    print(
        "\nHATA:"
    )

    print(
        hata
    )
