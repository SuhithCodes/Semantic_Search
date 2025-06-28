from flask import Flask, request, jsonify, render_template
import chromadb
from sentence_transformers import SentenceTransformer
import requests

# Initialize the Flask application
app = Flask(__name__)

# --- Pre-load Models and Database ---
# Load the sentence transformer model once when the app starts.
# This is more efficient than loading it on every request.
print("Loading sentence transformer model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded.")

# Initialize the ChromaDB client and get the collection.
print("Connecting to ChromaDB...")
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection(name="stackoverflow")
print("Connected to ChromaDB.")
# --- End Pre-loading ---


@app.route('/')
def index():
    """
    Renders the main search page.
    """
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """
    Handles the search query from the frontend.
    """
    # Get the query from the JSON request body
    data = request.get_json()
    query = data.get('query', '')
    num_results = data.get('num_results', 5)

    if not query:
        return jsonify({"error": "Query cannot be empty."}), 400

    # Convert the query to a vector embedding
    query_embedding = model.encode([query]).tolist()

    # Perform the search in ChromaDB
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=num_results,
        include=["metadatas", "documents", "distances"]
    )

    # Format the results to be sent back as JSON
    response_data = {
        'ids': results['ids'][0],
        'titles': results['documents'][0],
        'distances': results['distances'][0],
        'metadatas': results['metadatas'][0]
    }

    return jsonify(response_data)

@app.route('/get_answer/<answer_id>')
def get_answer(answer_id):
    """
    Fetches an answer from the Stack Exchange API.
    """
    try:
        # The Stack Exchange API endpoint for fetching answers
        api_url = f"https://api.stackexchange.com/2.3/answers/{answer_id}"
        
        # Parameters for the API request
        # The 'filter' is important: it tells the API to include the answer body in the response.
        params = {
            'site': 'stackoverflow',
            'filter': '!nO_c2es(N5' # Filter to get the answer body
        }

        # Make the GET request to the API
        response = requests.get(api_url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        
        data = response.json()

        if data['items']:
            # Return the body of the first answer found
            answer_body = data['items'][0].get('body', 'Answer body not found.')
            return jsonify({'body': answer_body})
        else:
            return jsonify({'error': 'Answer not found.'}), 404

    except requests.exceptions.RequestException as e:
        # Handle network errors or bad responses
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True) 