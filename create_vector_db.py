import chromadb
import jsonlines
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

def main():
    """
    Main function to create and populate the vector database.
    """
    # Initialize ChromaDB client. We'll use a persistent client to store the data on disk.
    client = chromadb.PersistentClient(path="./chroma_db")

    # Create a new collection or get it if it already exists.
    # The name of the collection is "stackoverflow"
    collection = client.get_or_create_collection(
        name="stackoverflow",
        metadata={"hnsw:space": "cosine"} # Using cosine distance for similarity
    )

    # Load a pre-trained sentence transformer model.
    # 'all-MiniLM-L6-v2' is a good model for semantic search.
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # We'll process the data in batches to be more efficient.
    batch_size = 100
    batch_ids = []
    batch_documents = []
    batch_metadatas = []

    print("Processing JSON file and creating vector embeddings with full metadata...")

    # Open the JSONL file and process it line by line.
    with jsonlines.open('stackoverflow-data-idf.json') as reader:
        for item in tqdm(reader, desc="Processing questions"):
            doc_id = item.get('id')
            title = item.get('title')

            if doc_id and title:
                # Prepare metadata by copying the entire item
                metadata = item.copy()
                
                # The 'id' and 'title' are already stored as top-level concepts in ChromaDB,
                # so we can remove them from the metadata dictionary to avoid redundancy.
                if 'id' in metadata:
                    del metadata['id']
                if 'title' in metadata:
                    del metadata['title']
                
                # Ensure all metadata values are of a supported type (str, int, float)
                for key, value in metadata.items():
                    if not isinstance(value, (str, int, float)):
                        metadata[key] = str(value)

                batch_ids.append(doc_id)
                batch_documents.append(title)
                batch_metadatas.append(metadata)

                # When the batch is full, process it.
                if len(batch_ids) >= batch_size:
                    embeddings = model.encode(batch_documents, show_progress_bar=False).tolist()
                    collection.upsert(
                        ids=batch_ids,
                        documents=batch_documents,
                        embeddings=embeddings,
                        metadatas=batch_metadatas
                    )
                    batch_ids = []
                    batch_documents = []
                    batch_metadatas = []

    # Process the last remaining batch if it's not empty.
    if batch_ids:
        embeddings = model.encode(batch_documents, show_progress_bar=False).tolist()
        collection.upsert(
            ids=batch_ids,
            documents=batch_documents,
            embeddings=embeddings,
            metadatas=batch_metadatas
        )

    print("\nVector database updated successfully with full metadata!")
    print(f"Total documents in collection: {collection.count()}")

if __name__ == "__main__":
    main() 