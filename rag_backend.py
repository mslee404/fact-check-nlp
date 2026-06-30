import json
import sqlite3
import sqlite_vec
import numpy as np
from fastembed import TextEmbedding

# =====================================================================
# 1. INIT EMBEDDING MODEL (Menggunakan BAAI/bge-m3 untuk Bahasa Indo)
# =====================================================================
print("Loading embedding model (FastEmbed)...")
# Model ini otomatis didownload saat pertama kali dijalankan
embedding_model = TextEmbedding("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# =====================================================================
# 2. SETUP DATABASE & EXTENSION (sqlite-vec)
# =====================================================================
def init_db(db_path="health_rag.db"):
    # Konek ke SQLite biasa
    conn = sqlite3.connect(db_path)
    
    # Kunci utama: Load ekstensi sqlite-vec agar SQLite support vector search
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    
    cursor = conn.cursor()
    
    # Hapus tabel lama jika mau reset data
    cursor.execute("DROP TABLE IF EXISTS health_articles")
    
    # Buat tabel untuk menyimpan metadata artikel dan embedding-nya
    # Model bge-m3 menghasilkan dimensi vektor sebesar 1024
    cursor.execute("""
        CREATE TABLE health_articles (
            id TEXT PRIMARY KEY,
            title TEXT,
            content TEXT,
            source TEXT,
            url TEXT,
            embedding BLOB
        )
    """)
    conn.commit()
    return conn


# =====================================================================
# 3. POPULATE DATABASE DARI FILE JSON
# =====================================================================
def populate_vector_db(json_path="knowledge_base_fixed.json", db_path="health_rag.db"):
    conn = init_db(db_path)
    cursor = conn.cursor()
    
    # Baca file json yang udah difix kemarin
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    articles = data.get("knowledge_base", [])
    print(f"Mengonversi {len(articles)} artikel ke format vektor...")
    
    for art in articles:
        doc_id = art["id"]
        title = art["title"]
        content = art["content"]
        source = art["source"]
        url = art["url"]
        
        # Proses embedding teks 'content' menggunakan FastEmbed
        # .embed() mengembalikan generator, kita ambil hasil pertamanya
        embedding_generator = embedding_model.embed([content])
        vector = next(embedding_generator)
        
        # sqlite-vec menyimpan vektor dalam bentuk binary (serialize array float32)
        vector_blob = np.array(vector, dtype=np.float32).tobytes()
        
        # Simpan ke database
        cursor.execute("""
            INSERT INTO health_articles (id, title, content, source, url, embedding)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (doc_id, title, content, source, url, vector_blob))
        
    conn.commit()
    conn.close()
    print("Database Vector SQLite berhasil dibuat dan diisi!")


# =====================================================================
# 4. ALUR RETRIEVAL (Fungsi yang akan dipakai oleh Husna / Streamlit)
# =====================================================================
def retrieve_context(query_text, top_k=3, db_path="health_rag.db"):
    """
    Fungsi untuk menerima klaim kesehatan user, mencari artikel paling mirip,
    dan mengembalikan konteks teks beserta sumbernya.
    """
    # 1. Embed query dari user menggunakan model yang sama
    query_vector_gen = embedding_model.embed([query_text])
    query_vector = next(query_vector_gen)
    query_blob = np.array(query_vector, dtype=np.float32).tobytes()
    
    # 2. Konek ke database dan load ekstensi vec
    conn = sqlite3.connect(db_path)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    
    cursor = conn.cursor()
    
    # 3. Lakukan Vector Search menggunakan Cosine Distance (vec_distance_cosine)
    # Kita cari nilai jarak terkecil (paling mirip)
    cursor.execute("""
        SELECT id, title, content, source, url, vec_distance_cosine(embedding, ?) AS distance
        FROM health_articles
        ORDER BY distance ASC
        LIMIT ?
    """, (query_blob, top_k))
    
    results = cursor.fetchall()
    conn.close()
    
    # 4. Rapikan hasil pencarian untuk dikonsumsi LLM
    retrieved_chunks = []
    metadata_list = []
    
    for row in results:
        doc_id, title, content, source, url, distance = row
        retrieved_chunks.append(content)
        metadata_list.append({
            "title": title,
            "source": source,
            "url": url,
            "score": round(1 - distance, 4) # Mengubah jarak menjadi score kemiripan
        })
        
    # Gabungkan semua teks artikel yang relevan menjadi satu string konteks besar
    full_context = "\n\n".join(retrieved_chunks)
    
    return full_context, metadata_list