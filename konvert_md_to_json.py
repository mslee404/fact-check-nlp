import json

# 1. Baca file MD mentah
with open("50_artikel_mitos_kesehatan_indonesia.md", "r", encoding="utf-8") as f:
    lines = f.readlines()

knowledge_base = []

for line in lines:
    # Hanya ambil baris yang merupakan isi tabel (diawali dan diakhiri dengan '|')
    if line.strip().startswith("|") and line.strip().endswith("|"):
        # Split berdasarkan karakter '|'
        parts = [p.strip() for p in line.split("|")]
        
        # Pastikan baris tersebut berisi data (bukan header atau separator tabel '---|---')
        if len(parts) >= 5 and parts[1].isdigit():
            doc_id = f"doc_{int(parts[1]):03d}"
            raw_title_text = parts[2]
            source = parts[3]
            url = parts[4]
            
            # Pembersihan teks mitos agar seragam dan rapi
            mitos_text = raw_title_text
            if "—" in raw_title_text:
                # Ambil bagian setelah tanda strip panjang
                mitos_text = raw_title_text.split("—")[1].strip()
            
            # Bersihkan sisa keyword pengganggu di teks
            mitos_text = mitos_text.replace("termasuk:", "").replace("mitos:", "").replace("(debunk)", "").strip()
            
            # Ambil judul utama (bagian sebelum strip panjang) sebagai title
            title = raw_title_text.split("—")[0].strip() if "—" in raw_title_text else raw_title_text
            
            # Generate kata kunci sederhana untuk metadata
            keywords = [kw.lower().replace("?", "").replace(",", "") for kw in title.split() if len(kw) > 3][:5]
            
            # Buat objek dokumen sesuai format yang kamu mau
            doc_obj = {
                "id": doc_id,
                "title": title,
                "content": f"Artikel dari {source} membahas tentang '{title}'. Klaim atau mitos yang beredar di masyarakat: {mitos_text}. Info lebih lanjut bisa diakses di {url}.",
                "source": source,
                "url": url,
                "label": "mitos",
                "mitos_text": mitos_text,
                "keywords": keywords
            }
            knowledge_base.append(doc_obj)

# 2. Simpan menjadi file JSON yang utuh
output_json = {"knowledge_base": knowledge_base}

with open("knowledge_base_fixed.json", "w", encoding="utf-8") as f:
    json.dump(output_json, f, indent=4, ensure_ascii=False)

print(f"Selesai! Berhasil mengekstrak {len(knowledge_base)} artikel ke dalam JSON.")