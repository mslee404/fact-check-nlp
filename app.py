import streamlit as st
# Import fungsi retrieval dari file backend yang udah kamu bikin kemarin
from rag_backend import retrieve_context
from groq import Groq
import os

# =====================================================================
# [TUGAS HUSNA] - INTEGRASI LLM GROQ & PROMPT ENGINEERING
# =====================================================================

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_llm_answer(query, context):
    prompt = f"""Kamu adalah sistem fact-checker kesehatan berbahasa Indonesia.
Berdasarkan konteks dari sumber terpercaya berikut, tentukan apakah klaim berikut adalah MITOS atau FAKTA.

Konteks:
{context}

Klaim yang diperiksa:
{query}

Jawab dengan format:
- Verdict: MITOS / FAKTA
- Penjelasan: (berdasarkan konteks di atas)
- Sumber: (sebutkan dari konteks mana)
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,  # rendah biar jawabannya konsisten & tidak kreatif
    )

    return response.choices[0].message.content


# =====================================================================
# [TUGAS SALSA] - UI INTERFACE STREAMLIT (CHATBOT WEBSITE)
# =====================================================================
def main():
    # Setup judul dan konfigurasi halaman utama
    st.set_page_config(page_title="Fact-Checking Kesehatan Indonesia", page_icon="🩺", layout="centered")
    
    st.title("🩺 Health Fact-Checker AI")
    st.write("Sistem Verifikasi Mitos & Fakta Kesehatan di Indonesia berbasis RAG (Llama 3.1 & SQLite-Vec)")
    st.caption("Oleh: Husna Nafi'ah & Salsabilla Fatika Subagyo (Data Science UNS)")
    st.write("---")
    
    # Input box untuk klaim kesehatan dari user
    user_query = st.text_input(
        "Masukkan Klaim/Mitos Kesehatan yang ingin kamu cek:",
        placeholder="Misal: Apakah benar makan mie instan campur nasi bikin diabetes?"
    )
    
    if st.button("Verifikasi Klaim", type="primary"):
        if user_query.strip() == "":
            st.warning("Silakan masukkan klaim kesehatan terlebih dahulu!")
        else:
            with st.spinner("Sistem sedang mencari artikel referensi dan menganalisis..."):
                try:
                    # 1. Jalankan fungsi retrieval milik Salsa
                    context, metadata = retrieve_context(user_query, top_k=3)
                    
                    if not context.strip():
                        st.error("Maaf, tidak ditemukan artikel referensi yang relevan di database.")
                        return
                    
                    # 2. Jalankan fungsi LLM milik Husna
                    llm_response = generate_llm_answer(user_query, context)
                    
                    # 3. Tampilkan Hasil Analisis LLM
                    st.success("Analisis Selesai!")
                    st.markdown(llm_response)
                    
                    # 4. Tampilkan Sumber Artikel Medis Tradisional (Metadata RAG)
                    st.write("---")
                    st.subheader("📚 Sumber Referensi Medis Terpercaya:")
                    for i, meta in enumerate(metadata, 1):
                        with st.expander(f"{i}. {meta['title']} ({meta['source']})"):
                            st.write(f"**Skor Kemiripan:** {meta['score']}")
                            st.write(f"**Link Artikel:** [{meta['url']}]({meta['url']})")
                            
                except Exception as e:
                    st.error(f"Terjadi kesalahan sistem: {e}")

if __name__ == "__main__":
    main()