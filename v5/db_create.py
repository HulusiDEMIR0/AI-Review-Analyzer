from sentence_transformers import SentenceTransformer
import chromadb
import json
import os

# =========================
# AYARLAR
# =========================
MODEL_NAME = "fredoline005/ajan-embed-q"

SAMSUNG_JSON = "./v5/veriler/Samsung_FE_25.json"
IPHONE_JSON = "./v5/veriler/İphone_17.json"

SAMSUNG_DB = "./v5/veriler/ajan_embed_q/Samsung_FE_25_chroma_db"
IPHONE_DB = "./v5/veriler/ajan_embed_q/İphone_17_chroma_db"

COLLECTION_NAME = "trendyol_yorumlari"
BATCH_SIZE = 32


# =========================
# MODEL
# =========================
print("Model yükleniyor...")
model = SentenceTransformer(MODEL_NAME)
print("Model hazır.")


# =========================
# VERİ YÜKLEME
# =========================
def load_reviews(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    reviews = data["yorumlar"]

    texts = [review["yorum"] for review in reviews]

    metadatas = [
        {
            "puan": str(review.get("puan", "")),
            "satici": str(review.get("satici", "")),
            "tarih": str(review.get("tarih", "")),
            "urun": str(review.get("urun", ""))
        }
        for review in reviews
    ]

    ids = [
        f"review_{i}"
        for i in range(len(texts))
    ]

    return texts, metadatas, ids


# =========================
# CHROMA DB OLUŞTUR
# =========================
def create_database(json_path, db_path, product_name):

    print(f"\n{'=' * 60}")
    print(f"{product_name} DB oluşturuluyor")
    print(f"{'=' * 60}")

    texts, metadatas, ids = load_reviews(json_path)

    print(f"Toplam yorum: {len(texts)}")

    os.makedirs(db_path, exist_ok=True)

    client = chromadb.PersistentClient(path=db_path)

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    # Önceden oluşturulmuşsa tekrar eklememek için
    if collection.count() > 0:
        print(f"DB zaten {collection.count()} kayıt içeriyor.")
        print("Yeni kayıt eklenmedi.")
        return

    print("Embedding oluşturuluyor...")

    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        normalize_embeddings=True,
        show_progress_bar=True
    ).tolist()

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )

    print(f"DB tamamlandı. Kayıt sayısı: {collection.count()}")


# =========================
# DB'LERİ OLUŞTUR
# =========================
create_database(
    SAMSUNG_JSON,
    SAMSUNG_DB,
    "Samsung FE 25"
)

create_database(
    IPHONE_JSON,
    IPHONE_DB,
    "iPhone 17"
)

print("\nTÜM DB'LER OLUŞTURULDU.")