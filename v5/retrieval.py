from sentence_transformers import SentenceTransformer
import chromadb


# =========================
# AYARLAR
# =========================

MODEL_NAME = "fredoline005/ajan-embed-q"

SAMSUNG_DB = "./v5/veriler/ajan_embed_q/Samsung_FE_25_chroma_db"
IPHONE_DB = "./v5/veriler/ajan_embed_q/İphone_17_chroma_db"

COLLECTION_NAME = "trendyol_yorumlari"
TOP_K = 5


# =========================
# MODEL
# =========================

print("Model yükleniyor...")

model = SentenceTransformer(MODEL_NAME)

print("Model hazır.")


# =========================
# CHROMA
# =========================

samsung_client = chromadb.PersistentClient(path=SAMSUNG_DB)
iphone_client = chromadb.PersistentClient(path=IPHONE_DB)

samsung_collection = samsung_client.get_collection(COLLECTION_NAME)
iphone_collection = iphone_client.get_collection(COLLECTION_NAME)


# =========================
# RETRIEVAL
# =========================

def search(collection, soru):

    # Ajan-Embed-Q için query formatı
    query = "query: " + soru

    embedding = model.encode(
        query,
        normalize_embeddings=True
    ).tolist()

    results = collection.query(
        query_embeddings=[embedding],
        n_results=TOP_K,
        include=[
            "documents",
            "distances",
            "metadatas"
        ]
    )

    return results