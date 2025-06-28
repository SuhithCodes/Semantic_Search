import chromadb
from sentence_transformers import SentenceTransformer
import argparse
from datetime import datetime

def main():
    """
    Main function to perform a semantic search on the vector database.
    """
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Search for questions in the Stack Overflow vector database.")
    parser.add_argument("query", type=str, help="The search query.")
    parser.add_argument("-n", "--num_results", type=int, default=5, help="Number of results to return.")
    args = parser.parse_args()

    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection(name="stackoverflow")

    # Load the sentence transformer model
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Convert the query to a vector embedding
    query_embedding = model.encode([args.query]).tolist()

    # Perform the search with metadata
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=args.num_results,
        include=["metadatas", "documents", "distances"]
    )

    print(f"Found {len(results['ids'][0])} results for '{args.query}':\n")

    # Print the results with all metadata
    for i, doc_id in enumerate(results['ids'][0]):
        distance = results['distances'][0][i]
        document = results['documents'][0][i]
        metadata = results['metadatas'][0][i] or {}
        
        print(f"Result {i+1}:")
        print(f"  ID: {doc_id}")
        print(f"  Title: {document}")
        print(f"  Distance: {distance:.4f}")
        
        # Display all available metadata
        if metadata:
            print(f"  Score: {metadata.get('score', 'N/A')}")
            print(f"  Answer Count: {metadata.get('answer_count', 'N/A')}")
            print(f"  Comment Count: {metadata.get('comment_count', 'N/A')}")
            print(f"  View Count: {metadata.get('view_count', 'N/A')}")
            
            # Format creation date
            if metadata.get('creation_date'):
                try:
                    creation_date = datetime.fromisoformat(metadata['creation_date'].replace('Z', '+00:00'))
                    print(f"  Created: {creation_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                except:
                    print(f"  Created: {metadata['creation_date']}")
            
            # Format last activity date
            if metadata.get('last_activity_date'):
                try:
                    last_activity = datetime.fromisoformat(metadata['last_activity_date'].replace('Z', '+00:00'))
                    print(f"  Last Activity: {last_activity.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                except:
                    print(f"  Last Activity: {metadata['last_activity_date']}")
            
            # Display tags
            if metadata.get('tags'):
                tags = metadata['tags'].split('|')
                print(f"  Tags: {', '.join(tags)}")
            
            # Display accepted answer ID if available
            if metadata.get('accepted_answer_id'):
                print(f"  Accepted Answer ID: {metadata['accepted_answer_id']}")
            
            # Display owner information
            if metadata.get('owner_user_id'):
                print(f"  Owner User ID: {metadata['owner_user_id']}")
                if metadata.get('owner_display_name'):
                    print(f"  Owner Name: {metadata['owner_display_name']}")
            
            # Display other metadata
            if metadata.get('favorite_count'):
                print(f"  Favorites: {metadata['favorite_count']}")
            
            if metadata.get('last_editor_user_id'):
                print(f"  Last Editor ID: {metadata['last_editor_user_id']}")
                if metadata.get('last_editor_display_name'):
                    print(f"  Last Editor: {metadata['last_editor_display_name']}")
            
            if metadata.get('last_edit_date'):
                try:
                    last_edit = datetime.fromisoformat(metadata['last_edit_date'].replace('Z', '+00:00'))
                    print(f"  Last Edited: {last_edit.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                except:
                    print(f"  Last Edited: {metadata['last_edit_date']}")
        
        print("-" * 60)

if __name__ == "__main__":
    main() 