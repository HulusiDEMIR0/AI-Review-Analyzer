class ConversationMemory:

    def __init__(self):
        self.messages = []

    # ========================================================
    # KULLANICI MESAJI EKLE
    # ========================================================

    def add_user_message(self, message):

        self.messages.append({
            "role": "user",
            "content": message
        })

    # ========================================================
    # ASİSTAN CEVABI EKLE
    # ========================================================

    def add_assistant_message(self, message):

        self.messages.append({
            "role": "assistant",
            "content": message
        })

    # ========================================================
    # TÜM HISTORY'Yİ GETİR
    # ========================================================

    def get_messages(self):

        return self.messages.copy()

    # ========================================================
    # HISTORY'Yİ TEXT OLARAK GETİR
    # ========================================================

    def get_history_text(self):

        if not self.messages:
            return "Henüz önceki konuşma bulunmamaktadır."

        lines = []

        for message in self.messages:

            if message["role"] == "user":
                lines.append(
                    f"KULLANICI: {message['content']}"
                )

            elif message["role"] == "assistant":
                lines.append(
                    f"ASİSTAN: {message['content']}"
                )

        return "\n\n".join(lines)

    # ========================================================
    # SON MESAJLARI GETİR
    # ========================================================

    def get_last_messages(self, count=10):

        return self.messages[-count:]

    # ========================================================
    # HISTORY TEMİZLE
    # ========================================================

    def clear(self):

        self.messages = []

    # ========================================================
    # MESAJ SAYISI
    # ========================================================

    def message_count(self):

        return len(self.messages)