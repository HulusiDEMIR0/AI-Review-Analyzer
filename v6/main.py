import time

from initial_context import create_initial_context
from conversation_memory import ConversationMemory
from generator import generate_answer


# ============================================================
# AYARLAR
# ============================================================

SHOW_INITIAL_CONTEXT_INFO = True

ANSWER_LOG_FILE = "./v6/veriler/cevaplar.txt"

# Geçmişten LLM'e gönderilecek maksimum mesaj sayısı.
# 4 mesaj = son 2 soru-cevap turu. Tüm geçmişi göndermek prompt'u
# her turda büyütüp süreyi katlanarak artırıyordu (bkz. eski
# cevaplar.txt: 107s -> 239s). "Peki", "hangisi" gibi eksiltili
# ifadeleri çözmek için son 2 tur yeterli; daha eskisi gerekmiyor.
MAX_HISTORY_MESSAGES = 4


# ============================================================
# GEÇMİŞİ SINIRLI METNE ÇEVİR
# ============================================================

def get_limited_history_text(memory, max_messages=MAX_HISTORY_MESSAGES):

    recent_messages = memory.get_last_messages(max_messages)

    if not recent_messages:
        return "Henüz önceki konuşma bulunmamaktadır."

    lines = []

    for message in recent_messages:

        if message["role"] == "user":
            lines.append(f"KULLANICI: {message['content']}")

        elif message["role"] == "assistant":
            lines.append(f"ASİSTAN: {message['content']}")

    return "\n\n".join(lines)


# ============================================================
# TEST SORULARI
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


# ============================================================
# CEVAP DOSYASINA YAZ
# ============================================================

def write_answer(log_file, test_no, question, answer, generation_time):

    log_file.write("\n")
    log_file.write("=" * 80 + "\n")
    log_file.write(f"TEST {test_no}/6\n")
    log_file.write("=" * 80 + "\n")

    log_file.write("\nSORU:\n")
    log_file.write(question + "\n")

    log_file.write("\nCEVAP:\n")
    log_file.write(answer + "\n")

    log_file.write("\nLLM SÜRESİ:\n")
    log_file.write(f"{generation_time:.4f} saniye\n")

    log_file.flush()


# ============================================================
# ANA PROGRAM
# ============================================================

def main():

    print("=" * 70)
    print("AI REVIEW ANALYZER - V6")
    print("CONTINUOUS CONTEXT + CONVERSATION MEMORY")
    print("=" * 70)

    # ========================================================
    # 1. INITIAL CONTEXT
    # ========================================================

    print("\n[1] Ürün verileri yükleniyor...")

    context_start = time.perf_counter()

    initial_context = create_initial_context()

    context_time = time.perf_counter() - context_start

    print(
        f"✓ Initial Context oluşturuldu "
        f"({context_time:.4f} saniye)"
    )

    if SHOW_INITIAL_CONTEXT_INFO:

        context_chars = len(initial_context)

        print(
            f"✓ Initial Context uzunluğu: "
            f"{context_chars:,} karakter"
        )

    # ========================================================
    # 2. CONVERSATION MEMORY
    # ========================================================

    memory = ConversationMemory()

    print("✓ Conversation Memory oluşturuldu")

    # ========================================================
    # 3. CEVAP DOSYASI
    # ========================================================

    with open(ANSWER_LOG_FILE, "w", encoding="utf-8") as answer_file:

        answer_file.write("=" * 80 + "\n")
        answer_file.write("AI REVIEW ANALYZER - V6 TEST CEVAPLARI\n")
        answer_file.write("CONTINUOUS CONTEXT + CONVERSATION MEMORY\n")
        answer_file.write("=" * 80 + "\n")

        # ====================================================
        # 4. TEST DÖNGÜSÜ
        # ====================================================

        for test_no, question in enumerate(TEST_QUESTIONS, start=1):

            print("")
            print("=" * 70)
            print(f"[TEST {test_no}/6]")
            print("=" * 70)
            print(f"SORU: {question}")

            print("\nLLM cevap oluşturuyor...")

            start_time = time.perf_counter()

            try:

                # Önceki konuşma history'sini al
                # (tüm geçmiş değil, sadece son MAX_HISTORY_MESSAGES
                # mesaj - bkz. dosya başındaki not)
                history_text = get_limited_history_text(memory)

                # LLM
                answer = generate_answer(
                    initial_context=initial_context,
                    conversation_history=history_text,
                    current_question=question
                )

                generation_time = time.perf_counter() - start_time

            except Exception as e:

                print("\n✗ HATA:")
                print(e)

                answer_file.write("\n")
                answer_file.write("=" * 80 + "\n")
                answer_file.write(f"TEST {test_no}/6 - HATA\n")
                answer_file.write("=" * 80 + "\n")
                answer_file.write(f"SORU:\n{question}\n")
                answer_file.write(f"HATA:\n{e}\n")
                answer_file.flush()

                # Soru yine de memory'ye eklenir; aksi halde bir
                # sonraki soru "hangisi", "bu" gibi eksiltili
                # ifadelerle bağlamsız kalır (bkz. önceki Test 5/6).
                memory.add_user_message(question)
                memory.add_assistant_message(
                    "(Bu soruya teknik bir hata nedeniyle cevap üretilemedi.)"
                )

                continue

            # =================================================
            # CEVAP
            # =================================================

            print("")
            print("AI:")
            print(answer)

            print("")
            print(
                f"[LLM süresi: {generation_time:.4f} saniye]"
            )

            # =================================================
            # DOSYAYA KAYDET
            # =================================================

            write_answer(
                log_file=answer_file,
                test_no=test_no,
                question=question,
                answer=answer,
                generation_time=generation_time
            )

            # =================================================
            # MEMORY'YE EKLE
            # =================================================

            memory.add_user_message(question)
            memory.add_assistant_message(answer)

            print(
                f"[Conversation Memory: "
                f"{memory.message_count()} mesaj]"
            )

    # ========================================================
    # TESTLER TAMAMLANDI
    # ========================================================

    print("")
    print("=" * 70)
    print("6 TEST TAMAMLANDI")
    print(f"Cevaplar kaydedildi: {ANSWER_LOG_FILE}")
    print("=" * 70)


# ============================================================
# PROGRAM BAŞLANGICI
# ============================================================

if __name__ == "__main__":
    main()