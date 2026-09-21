import json


SAMSUNG_TECHNICAL_FILE = "./v5/veriler/samsung_galaxy_s25_fe_epey.json"
IPHONE_TECHNICAL_FILE = "./v5/veriler/apple_iphone_17_epey.json"

SAMSUNG_REVIEW_FILE = "./v5/veriler/Samsung_FE_25.json"
IPHONE_REVIEW_FILE = "./v5/veriler/İphone_17.json"


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


def load_product_info(product):
    files = PRODUCT_FILES.get(product)

    if not files:
        return {}

    with open(files["technical"], "r", encoding="utf-8") as f:
        technical_data = json.load(f)

    with open(files["reviews"], "r", encoding="utf-8") as f:
        review_data = json.load(f)

    return {
        "fiyat": technical_data.get("fiyat"),
        "trendyol_ai_ozet": review_data.get("trendyol_ai_ozet"),
        "istatistikler": review_data.get("istatistikler", {})
    }


def build_context(question, products, retrieved_reviews, technical_results):

    context = {
        "question": question,
        "products": {}
    }

    for product in products:

        product_context = {
            "reviews": [],
            "technical_data": {},
            "product_info": load_product_info(product)
        }

        # Retriever'dan gelen yorumlar
        reviews = retrieved_reviews.get(product, [])

        for review in reviews:
            product_context["reviews"].append({
                "distance": review["distance"],
                "text": review["document"]
            })

        # Technical Data'dan gelen teknik bilgiler
        technical_data = technical_results.get(product)

        if technical_data is not None:
            product_context["technical_data"] = technical_data

        context["products"][product] = product_context

    return context


def context_to_text(context):

    text = []

    text.append("==================================================")
    text.append("KULLANICI SORUSU")
    text.append("==================================================")
    text.append(context["question"])

    text.append("")
    text.append("==================================================")
    text.append("ÜRÜN VERİLERİ")
    text.append("==================================================")

    for product, data in context["products"].items():

        product_name = PRODUCT_NAMES.get(product, product)

        text.append("")
        text.append("##################################################")
        text.append(f"ÜRÜN: {product_name}")
        text.append(f"ÜRÜN KODU: {product}")
        text.append("##################################################")

        # Kullanıcı yorumları
        text.append("")
        text.append("--- SADECE BU ÜRÜNE AİT KULLANICI YORUMLARI ---")

        if data["reviews"]:

            for i, review in enumerate(data["reviews"], start=1):
                text.append(f"{i}. {review['text']}")

        else:
            text.append("Kullanıcı yorumu bulunamadı.")

        # Teknik veriler
        text.append("")
        text.append("--- SADECE BU ÜRÜNE AİT TEKNİK VERİLER ---")

        if data["technical_data"]:

            text.append(
                json.dumps(
                    data["technical_data"],
                    ensure_ascii=False,
                    indent=2
                )
            )

        else:
            text.append("Teknik veri bulunamadı.")

        # Ürün bilgileri
        text.append("")
        text.append("--- SADECE BU ÜRÜNE AİT ÜRÜN BİLGİLERİ ---")

        text.append(
            json.dumps(
                data["product_info"],
                ensure_ascii=False,
                indent=2
            )
        )

        text.append("")
        text.append(f"--- {product_name} VERİLERİNİN SONU ---")

    return "\n".join(text)