import json
import time
import io
from contextlib import redirect_stdout

from query_analyzer import analyze_query, get_user_message
from retrieval import search, samsung_collection, iphone_collection
from technical_data import analyze_technical_topic, get_topic_data
from context_builder import build_context, context_to_text
from v5.generator1 import generate_answer


# ============================================================
# AYARLAR
# ============================================================

TEST_QUESTIONS = [
    "Samsung FE 25'in ekranı nasıl?",
    "Samsung FE 25'in bataryası nasıl?",
    "iPhone 17'nin kamerası nasıl?",
    "iPhone 17'nin tasarımı nasıl?",
    "Samsung FE 25'in temel donanımı nasıl?",
    "Samsung FE 25'in ekran yenileme hızı kaç Hz?",
    "Samsung FE 25'in dahili depolama seçenekleri neler?",
    "iPhone 17'nin kamera çözünürlüğü kaç MP?",
    "iPhone 17'nin optik görüntü sabitleyicisi var mı?",
    "Samsung FE 25'in 3x optik zoom özelliği var mı?",
    "iPhone 17'nin kamerası mı daha iyi Samsung FE 25'in kamerası mı?",
    "Samsung FE 25 mi iPhone 17 mi daha uzun pil ömrü sunuyor?",
    "iPhone 17 mi Samsung FE 25 mi daha iyi ekrana sahip?",
    "Samsung FE 25 mi iPhone 17 mi daha iyi performans sunuyor?",
    "iPhone 17 ile Samsung FE 25 arasında hangisinin tasarımı daha iyi?"
]

LOG_FILE = "./v5/veriler/test_sonuclari.txt"


# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================

def print_terminal(message=""):
    print(message, flush=True)


def write_log(log_file, text=""):
    log_file.write(text + "\n")
    log_file.flush()


def run_and_capture(function, *args, **kwargs):
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        result = function(*args, **kwargs)
    return result, buffer.getvalue()


def write_stage_output(log_file, title, captured_output, returned_data=None):
    write_log(log_file, "")
    write_log(log_file, "=" * 80)
    write_log(log_file, title)
    write_log(log_file, "=" * 80)

    if captured_output.strip():
        write_log(log_file, captured_output.rstrip())

    if returned_data is not None:
        write_log(log_file, "")
        write_log(log_file, "DÖNEN VERİ:")
        try:
            write_log(
                log_file,
                json.dumps(returned_data, ensure_ascii=False, indent=4)
            )
        except TypeError:
            write_log(log_file, str(returned_data))


def get_product_collection(product):
    if product == "Samsung_FE_25":
        return samsung_collection, "SAMSUNG FE 25"
    if product == "İphone_17":
        return iphone_collection, "IPHONE 17"
    return None, product


# ============================================================
# ANA PROGRAM
# ============================================================

def main():

    total_start = time.perf_counter()

    with open(LOG_FILE, "w", encoding="utf-8") as log_file:

        write_log(log_file, "=" * 100)
        write_log(log_file, "AI REVIEW ANALYZER - 15 TEST SONUÇLARI")
        write_log(log_file, "=" * 100)
        write_log(log_file, "")
        write_log(log_file, "Query Analyzer, Technical Data, Retriever ve Final LLM sonuçları kaydedilir.")
        write_log(log_file, "Context Builder detayları ayrıca kaydedilmez.")
        write_log(log_file, "")

        print_terminal("=" * 70)
        print_terminal("AI REVIEW ANALYZER - 15 TEST")
        print_terminal("=" * 70)

        for test_no, question in enumerate(TEST_QUESTIONS, start=1):

            test_start = time.perf_counter()

            print_terminal("")
            print_terminal(f"[TEST {test_no}/15] {question}")

            write_log(log_file, "")
            write_log(log_file, "#" * 100)
            write_log(log_file, f"TEST {test_no}/15")
            write_log(log_file, f"SORU: {question}")
            write_log(log_file, "#" * 100)

            try:

                # ====================================================
                # 1. QUERY ANALYZER
                # ====================================================

                stage_start = time.perf_counter()

                result, captured = run_and_capture(
                    analyze_query,
                    question
                )

                stage_time = time.perf_counter() - stage_start

                write_stage_output(
                    log_file,
                    "[1] QUERY ANALYZER",
                    captured,
                    result
                )

                message = get_user_message(result)

                if message:
                    print_terminal("  ✓ Query Analyzer tamamlandı")
                    print_terminal(f"  → Sistem: {message}")

                    write_log(log_file, "")
                    write_log(log_file, "SİSTEM MESAJI:")
                    write_log(log_file, message)

                    test_time = time.perf_counter() - test_start

                    write_log(log_file, "")
                    write_log(log_file, f"TEST SÜRESİ: {test_time:.4f} saniye")

                    print_terminal(f"  ✓ Test süresi: {test_time:.4f} sn")
                    continue

                print_terminal("  ✓ Query Analyzer tamamlandı")

                products = result["products"]

                # ====================================================
                # 2. TECHNICAL DATA
                # ====================================================

                stage_start = time.perf_counter()

                technical_result, captured = run_and_capture(
                    analyze_technical_topic,
                    question,
                    products
                )

                stage_time = time.perf_counter() - stage_start

                # Ham Gemma cevabı + Python sonucu korunuyor.
                write_stage_output(
                    log_file,
                    "[2] TECHNICAL DATA",
                    captured,
                    technical_result
                )

                write_log(
                    log_file,
                    f"Technical Data Süresi: {stage_time:.4f} saniye"
                )

                print_terminal("  ✓ Technical Data tamamlandı")

                # ====================================================
                # 3. RETRIEVER + TEKNİK VERİ
                # ====================================================

                retrieved_reviews = {}
                technical_results = {}

                for product in products:

                    collection, product_name = get_product_collection(product)

                    if collection is None:
                        continue

                    # ------------------------------------------------
                    # RETRIEVER
                    # ------------------------------------------------

                    stage_start = time.perf_counter()

                    results, captured = run_and_capture(
                        search,
                        collection,
                        question
                    )

                    stage_time = time.perf_counter() - stage_start

                    distances = results["distances"][0]
                    documents = results["documents"][0]

                    retrieved_reviews[product] = []

                    for distance, document in zip(distances, documents):
                        retrieved_reviews[product].append({
                            "distance": distance,
                            "document": document
                        })

                    # Retriever yalnızca bir kez yazılıyor.
                    write_stage_output(
                        log_file,
                        f"[3] {product_name} - RETRIEVER TOP 5",
                        captured,
                        results
                    )

                    write_log(
                        log_file,
                        f"Retriever Süresi: {stage_time:.4f} saniye"
                    )

                    # ------------------------------------------------
                    # TECHNICAL TOPIC + VERİ
                    # ------------------------------------------------

                    product_topic_result = technical_result["topics"].get(
                        product,
                        {}
                    )

                    topic = product_topic_result.get("topic")

                    technical_results[product] = None

                    write_log(log_file, "")
                    write_log(log_file, f"{product_name} - TEKNİK VERİ")

                    if topic is None:

                        write_log(
                            log_file,
                            "SEÇİLEN TOPIC: None"
                        )

                        write_log(
                            log_file,
                            "Teknik kategori bulunamadı."
                        )

                        print_terminal(
                            f"  ✓ {product_name} teknik kategori yok"
                        )

                        continue

                    technical_data = get_topic_data(
                        product,
                        topic
                    )

                    technical_results[product] = technical_data

                    write_log(
                        log_file,
                        f"SEÇİLEN TOPIC: {topic}"
                    )

                    write_log(
                        log_file,
                        "TEKNİK VERİ:"
                    )

                    write_log(
                        log_file,
                        json.dumps(
                            technical_data,
                            ensure_ascii=False,
                            indent=4
                        )
                    )

                    print_terminal(
                        f"  ✓ {product_name} Retriever + teknik veri tamamlandı"
                    )

                # ====================================================
                # 4. CONTEXT BUILDER
                # ====================================================

                context = build_context(
                    question,
                    products,
                    retrieved_reviews,
                    technical_results
                )

                context_text = context_to_text(context)

                # Context Builder çalışıyor fakat detayları loglanmıyor.
                print_terminal("  ✓ Context Builder tamamlandı")

                # ====================================================
                # 5. FINAL LLM
                # ====================================================

                stage_start = time.perf_counter()

                answer, captured = run_and_capture(
                    generate_answer,
                    context_text
                )

                stage_time = time.perf_counter() - stage_start

                # Final cevap yalnızca bir kez yazılıyor.
                write_log(log_file, "")
                write_log(log_file, "=" * 80)
                write_log(log_file, "[5] FINAL LLM")
                write_log(log_file, "=" * 80)
                write_log(log_file, "CEVAP:")
                write_log(log_file, answer)
                write_log(
                    log_file,
                    f"Final LLM Süresi: {stage_time:.4f} saniye"
                )

                # ====================================================
                # 6. TEST SONUCU
                # ====================================================

                test_time = time.perf_counter() - test_start

                write_log(log_file, "")
                write_log(log_file, "=" * 80)
                write_log(
                    log_file,
                    f"TEST SÜRESİ: {test_time:.4f} saniye"
                )
                write_log(log_file, "=" * 80)

                print_terminal("  ✓ Final LLM tamamlandı")
                print_terminal("  → CEVAP:")
                print_terminal(f"    {answer}")
                print_terminal(
                    f"  ✓ Test süresi: {test_time:.4f} sn"
                )

            except Exception as e:

                test_time = time.perf_counter() - test_start

                write_log(log_file, "")
                write_log(log_file, "=" * 80)
                write_log(log_file, "HATA")
                write_log(log_file, "=" * 80)
                write_log(log_file, repr(e))
                write_log(
                    log_file,
                    f"TEST SÜRESİ: {test_time:.4f} saniye"
                )

                print_terminal("  ✗ HATA")
                print_terminal(f"    {e}")
                print_terminal(
                    f"  ✓ Test süresi: {test_time:.4f} sn"
                )

        # ============================================================
        # TÜM TESTLER BİTTİ
        # ============================================================

        total_time = time.perf_counter() - total_start

        write_log(log_file, "")
        write_log(log_file, "#" * 100)
        write_log(log_file, "TÜM TESTLER TAMAMLANDI")
        write_log(log_file, f"TOPLAM SÜRE: {total_time:.4f} saniye")
        write_log(log_file, "#" * 100)

        print_terminal("")
        print_terminal("=" * 70)
        print_terminal("TÜM TESTLER TAMAMLANDI")
        print_terminal(f"Toplam süre: {total_time:.4f} sn")
        print_terminal(f"Detaylı sonuçlar: {LOG_FILE}")
        print_terminal("=" * 70)


if __name__ == "__main__":
    main()