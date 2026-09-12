from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingModel:
    def __init__(self):
        print(f"Loading embedding model: {MODEL_NAME}")
        self.model = SentenceTransformer(MODEL_NAME)

    def encode(self, texts):
        return self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True
        )

    def encode_query(self, query):
        return self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )[0]


if __name__ == "__main__":
    model = EmbeddingModel()

    embeddings = model.encode([
        "Python machine learning internship",
        "React frontend development internship"
    ])

    print("Embedding shape:", embeddings.shape)