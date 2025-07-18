from flask import Flask, request, jsonify, render_template
import chromadb
from sentence_transformers import SentenceTransformer
import requests
from bs4 import BeautifulSoup

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

@app.route('/scrape_answer/<question_id>')
def scrape_answer(question_id):
    """
    Scrapes the accepted or top answer for a given question ID from Stack Overflow.
    """
    try:
        url = f"https://stackoverflow.com/questions/{question_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Prioritize the accepted answer
        accepted_answer = soup.find('div', class_='accepted-answer')
        
        answer_body_html = None
        if accepted_answer:
            answer_body_html = accepted_answer.find('div', class_='s-prose js-post-body')
        else:
            # Fallback to the first answer if none is accepted
            answer_elements = soup.find_all('div', class_='answer')
            if answer_elements:
                answer_body_html = answer_elements[0].find('div', class_='s-prose js-post-body')

        if answer_body_html:
            return jsonify({'body': str(answer_body_html)})
        else:
            return jsonify({'error': 'Answer not found.'}), 404

    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/generate_ai_answer', methods=['POST'])
def generate_ai_answer():
    """
    Generates an AI answer using a local Llama model.
    """
    data = request.get_json()
    prompt = data.get('prompt', '')

    if not prompt:
        return jsonify({"error": "Prompt cannot be empty."}), 400

    try:
        # The local Llama API endpoint
        llama_api_url = "http://localhost:11434/api/chat"

        # The payload for the Llama API
        payload = {
            "model": "llama3.2:1b",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False
        }

        # Make the POST request to the Llama API
        response = requests.post(llama_api_url, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes

        llama_data = response.json()
        
        # Extract the content from the response
        ai_answer = llama_data.get('message', {}).get('content', 'AI answer not found.')

        return jsonify({'body': ai_answer})

    except requests.exceptions.RequestException as e:
        # Handle network errors or bad responses from Llama API
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True) 