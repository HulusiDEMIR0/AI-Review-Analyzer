import json
import re
import time
from playwright.sync_api import sync_playwright


print("=" * 60)
print("AI REVIEW ANALYZER - V2.1")
print("TRENDYOL YORUM + YILDIZ ANALİZİ")
print("=" * 60)


url = input("\nÜrün linkini gir: ").strip()

toplam_baslangic = time.perf_counter()


# ============================================================
# 1. ÜRÜN ID'SİNİ BUL
# ============================================================

print("\n[1/6] Ürün ID'si bulunuyor...")

match = re.search(r"-p-(\d+)", url)

if not match:
    print("HATA: Ürün ID'si linkten bulunamadı.")
    exit()

content_id = match.group(1)

print(f"      Ürün ID: {content_id}")


# ============================================================
# 2. TRENDYOL SAYFASINI AÇ
# ============================================================

print("\n[2/6] Trendyol sayfası açılıyor...")

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False
    )

    page = browser.new_page(
        viewport={"width": 1440, "height": 900}
    )

    ilk_veri = None

    # --------------------------------------------------------
    # Tarayıcının yaptığı ilk yorum API cevabını yakala
    # --------------------------------------------------------

    def response_handler(response):

        nonlocal_data = response.url

        if "product-reviews/detailed" not in nonlocal_data:
            return

        try:

            data = response.json()

            if (
                "result" in data
                and "reviews" in data["result"]
            ):
                global ilk_veri

                if ilk_veri is None:

                    ilk_veri = data

                    print("\n[API] İlk yorum isteği yakalandı!")

        except Exception:
            pass


    page.on("response", response_handler)


    # --------------------------------------------------------
    # Ürün sayfasını aç
    # --------------------------------------------------------

    print("      Sayfa açılıyor...")

    page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=30000
    )

    print("      Sayfa açıldı.")

    # Sayfanın ilk API isteklerini yapmasını bekle
    page.wait_for_timeout(7000)


    # --------------------------------------------------------
    # Yorum bölümünü tetikle
    # --------------------------------------------------------

    print("      Yorum bölümü yükleniyor...")

    page.mouse.wheel(
        0,
        5000
    )

    page.wait_for_timeout(5000)


    # --------------------------------------------------------
    # İlk API cevabı gelmiş mi?
    # --------------------------------------------------------

    if ilk_veri is None:

        print("\nHATA: İlk yorum verisi alınamadı.")

        browser.close()
        exit()


    # ========================================================
    # 3. TOPLAM YORUM SAYISINI BUL
    # ========================================================

    print("\n[3/6] Yorum sayıları alınıyor...")

    summary = ilk_veri["result"]["summary"]

    toplam_yorum = summary.get(
        "totalCommentCount",
        0
    )

    toplam_sayfa = summary.get(
        "totalPages",
        0
    )

    print(f"      Toplam yorum: {toplam_yorum}")
    print(f"      Toplam sayfa: {toplam_sayfa}")


    # ========================================================
    # 4. TÜM SAYFALARI TARA
    # ========================================================

    print("\n[4/6] Bütün yorumlar çekiliyor...")

    tum_veriler = []

    # İlk sayfa zaten elimizde
    tum_veriler.append(ilk_veri)


    # --------------------------------------------------------
    # Tarayıcının içinden API çağrısı yap
    # --------------------------------------------------------

    for sayfa in range(1, toplam_sayfa):

        print(
            f"      Sayfa {sayfa + 1}/{toplam_sayfa} "
            f"isteniyor..."
        )

        try:

            veri = page.evaluate(
                """
                async ({ contentId, pageNumber }) => {

                    const params = new URLSearchParams({
                        contentId: contentId,
                        page: String(pageNumber),
                        pageSize: "5",
                        channelId: "1"
                    });

                    const url =
                        "https://apigw.trendyol.com/" +
                        "discovery-storefront-trproductgw-service/api/" +
                        "review-read/product-reviews/detailed?" +
                        params.toString();

                    const response = await fetch(url, {
                        method: "GET",
                        credentials: "include"
                    });

                    if (!response.ok) {
                        throw new Error(
                            "HTTP " + response.status
                        );
                    }

                    return await response.json();
                }
                """,
                {
                    "contentId": content_id,
                    "pageNumber": sayfa
                }
            )

            tum_veriler.append(veri)

            review_count = len(
                veri["result"].get("reviews", [])
            )

            toplam_su_anki = sum(
                len(
                    veri2["result"].get("reviews", [])
                )
                for veri2 in tum_veriler
            )

            print(
                f"            {review_count} yorum geldi "
                f"→ toplam {toplam_su_anki}"
            )

        except Exception as hata:

            print(
                f"            HATA: Sayfa {sayfa + 1} alınamadı."
            )

            print(
                f"            {hata}"
            )


    browser.close()


# ============================================================
# 5. YORUMLARI TEMİZLE VE YILDIZLARI HESAPLA
# ============================================================

print("\n[5/6] Yorumlar ve yıldızlar işleniyor...")

yorumlar = []

gorulen_idler = set()


for veri in tum_veriler:

    reviews = veri["result"].get(
        "reviews",
        []
    )

    for review in reviews:

        yorum_id = review.get("id")

        yorum_metni = review.get(
            "comment",
            ""
        ).strip()

        puan = review.get("rate")

        if not yorum_metni:
            continue

        if yorum_id in gorulen_idler:
            continue

        gorulen_idler.add(
            yorum_id
        )

        yorumlar.append(
            {
                "id": yorum_id,
                "puan": puan,
                "yorum": yorum_metni,
                "tarih": review.get(
                    "createdAt"
                ),
                "satici": review.get(
                    "seller",
                    {}
                ).get("name")
            }
        )


# ------------------------------------------------------------
# Yıldız ortalaması
# ------------------------------------------------------------

puanlar = [
    yorum["puan"]
    for yorum in yorumlar
    if yorum["puan"] is not None
]


if puanlar:

    ortalama_puan = (
        sum(puanlar)
        / len(puanlar)
    )

else:

    ortalama_puan = None


# ------------------------------------------------------------
# Yıldız dağılımı
# ------------------------------------------------------------

yildiz_dagilimi = {}


for yildiz in range(5, 0, -1):

    adet = puanlar.count(
        yildiz
    )

    yuzde = (
        adet / len(puanlar) * 100
        if puanlar
        else 0
    )

    yildiz_dagilimi[str(yildiz)] = {
        "adet": adet,
        "yuzde": round(
            yuzde,
            2
        )
    }


# ============================================================
# 6. JSON'A KAYDET
# ============================================================

trendyol_ai_ozet = ilk_veri["result"].get("aiSummary", "")

veri = {
    "urun": {
        "content_id": content_id,
        "url": url
    },

    "trendyol_ai_ozet": trendyol_ai_ozet,

    "istatistikler": {
        "trendyol_toplam_yorum": toplam_yorum,
        "trendyol_toplam_sayfa": toplam_sayfa,
        "cekilen_yorum": len(yorumlar),
        "ortalama_puan": (
            round(ortalama_puan, 2)
            if ortalama_puan is not None
            else None
        ),
        "yildiz_dagilimi": yildiz_dagilimi
    },

    "yorumlar": yorumlar
}


with open(
    "İphone_17.json",
    "w",
    encoding="utf-8"
) as dosya:

    json.dump(
        veri,
        dosya,
        ensure_ascii=False,
        indent=4
    )


toplam_sure = (
    time.perf_counter()
    - toplam_baslangic
)


# ============================================================
# SONUÇ
# ============================================================

print("\n" + "=" * 60)
print("[6/6] V2.1 TAMAMLANDI")
print("=" * 60)

print(
    f"Ürün ID          : {content_id}"
)

print(
    f"Trendyol yorum   : {toplam_yorum}"
)

print(
    f"Çekilen yorum    : {len(yorumlar)}"
)

if ortalama_puan is not None:

    print(
        f"Ortalama puan    : "
        f"{ortalama_puan:.2f} / 5"
    )

print(
    f"Toplam süre      : "
    f"{toplam_sure:.2f} saniye"
)


print("\nYILDIZ DAĞILIMI")
print("-" * 60)

for yildiz in range(5, 0, -1):

    bilgi = yildiz_dagilimi[
        str(yildiz)
    ]

    print(
        f"{yildiz} yıldız → "
        f"{bilgi['adet']} yorum "
        f"(%{bilgi['yuzde']})"
    )


print("\nİLK 10 YORUM")
print("-" * 60)

for i, yorum in enumerate(
    yorumlar[:10],
    start=1
):

    print(
        f"\n{i}. "
        f"[{yorum['puan']}/5] "
        f"{yorum['satici']}"
    )

    print(
        yorum["yorum"]
    )


print(
    "\nVeriler 'yorumlar.json' "
    "dosyasına kaydedildi."
)