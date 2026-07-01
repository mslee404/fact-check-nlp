from fastembed import TextEmbedding

print("Downloading embedding model...")
model = TextEmbedding("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Paksa download dengan encode dummy
list(model.embed(["test"]))
print("Model downloaded successfully.")