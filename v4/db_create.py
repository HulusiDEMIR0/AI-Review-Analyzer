import json
import time

import chromadb
import ollama


# ============================================================
# AYARLAR
# ============================================================
EMBEDDING_MODEL = "bge-m3"
COLLECTION_NAME = "trendyol_yorumlari"

CHROMA_PATH = "./v4/chroma_db"


# ============================================================
# BAŞLANGIÇ
# ============================================================

baslangic = time.perf_counter()

print("=" * 60)
print("AI REVIEW ANALYZER - V4")
print("EMBEDDING + VECTOR DATABASE OLUŞTURMA")
print("=" * 60)


# ============================================================
# 1. YORUMLARI OKU
# ============================================================

print("\n[1/4] yorumlar.json okunuyor...")

with open(
    "./v4/yorumlar.json",
    "r",
    encoding="utf-8"
) as dosya:

    veri = json.load(dosya)


yorumlar = veri["yorumlar"]

print(
    f"      Toplam yorum: {len(yorumlar)}"
)


# ============================================================
# 2. CHROMADB OLUŞTUR / BAĞLAN
# ============================================================

print("\n[2/4] Vector database hazırlanıyor...")

client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME
)

print("      ChromaDB hazır.")


# ============================================================
# 3. YORUMLARI EMBEDDING'E ÇEVİR VE KAYDET
# ============================================================

print("\n[3/4] Yorumlar embedding'e dönüştürülüyor...")

for i, yorum in enumerate(
    yorumlar,
    start=1
):

    metin = yorum["yorum"]

    response = ollama.embed(
        model=EMBEDDING_MODEL,
        input=metin
    )

    embedding = response["embeddings"][0]

    collection.upsert(
        ids=[
            str(
                yorum["id"]
            )
        ],

        embeddings=[
            embedding
        ],

        documents=[
            metin
        ],

        metadatas=[
            {
                "puan": yorum["puan"],
                "satici": yorum["satici"],
                "tarih": yorum["tarih"]
            }
        ]
    )

    print(
        f"      {i}/{len(yorumlar)} → embedding hazır"
    )


# ============================================================
# 4. SONUÇ
# ============================================================

toplam_sure = (
    time.perf_counter()
    - baslangic
)

print("\n[4/4] Embedding işlemi tamamlandı.")

print(
    f"      Veritabanındaki kayıt: "
    f"{collection.count()}"
)

print(
    f"      Toplam süre: "
    f"{toplam_sure:.2f} saniye"
)

print("\n" + "=" * 60)
print("V4 EMBEDDING DATABASE HAZIR")
print("=" * 60)