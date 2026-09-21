import json


# ============================================================
# DOSYA YOLLARI
# ============================================================

SAMSUNG_TECHNICAL_FILE = "./v6/veriler/samsung_galaxy_s25_fe_epey.json"
IPHONE_TECHNICAL_FILE = "./v6/veriler/apple_iphone_17_epey.json"

SAMSUNG_REVIEW_FILE = "./v6/veriler/Samsung_FE_25.json"
IPHONE_REVIEW_FILE = "./v6/veriler/İphone_17.json"


# ============================================================
# ÜRÜNLER
# ============================================================

PRODUCT_FILES = {
    "Samsung_FE_25": {
        "technical": SAMSUNG_TECHNICAL_FILE,
        "reviews": SAMSUNG_REVIEW_FILE
    },
    "İphone_17": {
        "technical": IPHONE_TECHNICAL_FILE,
        "reviews": IPHONE_REVIEW_FILE
    }
}


PRODUCT_NAMES = {
    "Samsung_FE_25": "Samsung Galaxy S25 FE",
    "İphone_17": "iPhone 17"
}


# ============================================================
# JSON YÜKLEME
# ============================================================

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# ÜRÜN VERİLERİNİ YÜKLE
# ============================================================

def load_product_info(product):
    files = PRODUCT_FILES.get(product)

    if not files:
        raise ValueError(f"Bilinmeyen ürün: {product}")

    technical_data = load_json(files["technical"])
    review_data = load_json(files["reviews"])

    return {
        "product_name": PRODUCT_NAMES.get(product, product),

        # V5'te kullandığımız ürün bilgileri
        "fiyat": technical_data.get("fiyat"),
        "trendyol_ai_ozet": review_data.get("trendyol_ai_ozet"),
        "istatistikler": review_data.get("istatistikler", {}),

        # TÜM teknik veri
        "technical_data": technical_data,

        # TÜM kullanıcı yorumları
        "reviews": review_data
    }


# ============================================================
# INITIAL CONTEXT OLUŞTUR
# ============================================================

def build_initial_context():

    context = {
        "products": {}
    }

    for product in PRODUCT_FILES:

        product_data = load_product_info(product)

        context["products"][product] = product_data

    return context


# ============================================================
# CONTEXT → TEXT
# ============================================================

def initial_context_to_text(context):

    text = []

    text.append("=" * 80)
    text.append("AI REVIEW ANALYZER - INITIAL CONTEXT")
    text.append("=" * 80)

    text.append("")
    text.append(
        "Aşağıdaki bilgiler sistem tarafından başlangıçta yüklenmiştir."
    )

    text.append(
        "Bu bilgiler Samsung Galaxy S25 FE ve iPhone 17 ürünlerine aittir."
    )

    # --------------------------------------------------------
    # ÜRÜNLER
    # --------------------------------------------------------

    for product, data in context["products"].items():

        product_name = data["product_name"]

        text.append("")
        text.append("#" * 80)
        text.append(f"ÜRÜN: {product_name}")
        text.append(f"ÜRÜN KODU: {product}")
        text.append("#" * 80)

        # ----------------------------------------------------
        # KULLANICI YORUMLARI
        # ----------------------------------------------------

        text.append("")
        text.append(
            "--- SADECE BU ÜRÜNE AİT TÜM KULLANICI YORUMLARI ---"
        )

        reviews = data["reviews"]

        if isinstance(reviews, dict):

            # JSON'daki yorumların bulunduğu alanı bulmaya çalış
            if "yorumlar" in reviews:
                review_list = reviews["yorumlar"]

            elif "reviews" in reviews:
                review_list = reviews["reviews"]

            elif "comments" in reviews:
                review_list = reviews["comments"]

            else:
                review_list = []

        elif isinstance(reviews, list):
            review_list = reviews

        else:
            review_list = []

        if review_list:

            for i, review in enumerate(review_list, start=1):

                if isinstance(review, dict):

                    # Yaygın yorum alanlarını kontrol et
                    review_text = (
                        review.get("yorum")
                        or review.get("text")
                        or review.get("comment")
                        or review.get("content")
                        or str(review)
                    )

                else:
                    review_text = str(review)

                text.append(f"{i}. {review_text}")

        else:
            text.append("Kullanıcı yorumu bulunamadı.")

        # ----------------------------------------------------
        # TÜM TEKNİK VERİLER
        # ----------------------------------------------------

        text.append("")
        text.append(
            "--- SADECE BU ÜRÜNE AİT TÜM TEKNİK VERİLER ---"
        )

        technical_data = data["technical_data"]

        text.append(
            json.dumps(
                technical_data,
                ensure_ascii=False,
                indent=2
            )
        )

        # ----------------------------------------------------
        # FİYAT
        # ----------------------------------------------------

        text.append("")
        text.append("--- ÜRÜN FİYATI ---")
        text.append(str(data["fiyat"]))

        # ----------------------------------------------------
        # TRENDYOL AI ÖZETİ
        # ----------------------------------------------------

        text.append("")
        text.append("--- TRENDYOL AI ÖZETİ ---")

        text.append(
            json.dumps(
                data["trendyol_ai_ozet"],
                ensure_ascii=False,
                indent=2
            )
        )

        # ----------------------------------------------------
        # İSTATİSTİKLER
        # ----------------------------------------------------

        text.append("")
        text.append("--- TRENDYOL İSTATİSTİKLERİ ---")

        text.append(
            json.dumps(
                data["istatistikler"],
                ensure_ascii=False,
                indent=2
            )
        )

        text.append("")
        text.append(f"--- {product_name} VERİLERİNİN SONU ---")

    return "\n".join(text)


# ============================================================
# ANA FONKSİYON
# ============================================================

def create_initial_context():

    context = build_initial_context()

    context_text = initial_context_to_text(context)

    return context_text


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    context_text = create_initial_context()

    print("=" * 80)
    print("INITIAL CONTEXT KONTROL")
    print("=" * 80)

    print(f"Toplam context karakteri: {len(context_text):,}")

    print("\nSamsung Galaxy S25 FE bulundu:",
          "ÜRÜN: Samsung Galaxy S25 FE" in context_text)

    print("iPhone 17 bulundu:",
          "ÜRÜN: iPhone 17" in context_text)

    print("\nSamsung yorum sayısı:")
    print(context_text.count("SADECE BU ÜRÜNE AİT TÜM KULLANICI YORUMLARI"))

    print("\n" + "=" * 80)
    print("INITIAL CONTEXT BAŞARIYLA OLUŞTURULDU")
    print("=" * 80)