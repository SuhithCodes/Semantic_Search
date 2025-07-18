import requests
import os
import time
import json
import argparse
from bs4 import BeautifulSoup

def load_data(filename='data.json'):
    """Loads existing data from a JSON file."""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data, filename='data.json'):
    """Saves data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def get_last_scraped_id(filename='last_scraped.txt'):
    """Gets the last successfully scraped question ID."""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            content = f.read().strip()
            if content.isdigit():
                return int(content)
    return 1

def update_last_scraped_id(n, filename='last_scraped.txt'):
    """Updates the last successfully scraped question ID."""
    with open(filename, 'w') as f:
        f.write(str(n))

def scrape_stackoverflow(start_id, end_id, data_file='data.json', last_id_file='last_scraped.txt'):
    """
    Scrapes questions and answers from Stack Overflow.
    """
    data = load_data(data_file)
    
    print(f"Starting scrape from question ID: {start_id}")

    for n in range(start_id, end_id + 1):
        try:
            print(f"Scraping question ID: {n}...")
            url = f"https://stackoverflow.com/questions/{n}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()  # Will raise an HTTPError for bad responses (4xx or 5xx)

            soup = BeautifulSoup(r.content, 'html.parser')

            title_element = soup.find("title")
            if not title_element:
                print(f"  - No title found for ID {n}. Skipping.")
                continue

            title = title_element.text
            if "Page not found - Stack Overflow" in title:
                print(f"  - Page not found for ID {n}. Skipping.")
                continue

            # Find all potential answer containers
            answer_elements = soup.find_all("div", {"class": "s-prose js-post-body"})

            if len(answer_elements) < 2: # Expecting at least question body and one answer
                print(f"  - Not enough content (question/answer) for ID {n}. Skipping.")
                continue

            # The first element is the question body, the second is the first answer
            answer_text = answer_elements[1].get_text(separator='\n').strip()
            
            # Clean title
            title = title.replace(" - Stack Overflow", "").strip()

            # Add to our data
            data[title] = answer_text
            print(f"  - Success! Title: '{title}' | Data length: {len(data)}")

            update_last_scraped_id(n, last_id_file)

            # Save progress periodically
            if n % 5 == 0:
                save_data(data, data_file)
                print(f"  - Progress saved to {data_file}")

        except requests.exceptions.HTTPError as e:
            print(f"  - HTTP Error for ID {n}: {e}. Skipping.")
        except requests.exceptions.RequestException as e:
            print(f"  - Request failed for ID {n}: {e}. Retrying might be necessary.")
        except Exception as e:
            print(f"  - An unexpected error occurred for ID {n}: {e}")
        
        # Be a good web citizen
        time.sleep(5)
    
    # Final save
    save_data(data, data_file)
    print("\nScraping finished. Final data saved.")

def main():
    parser = argparse.ArgumentParser(description="Scrape Stack Overflow questions and answers.")
    parser.add_argument('--start', type=int, help="The question ID to start scraping from. Defaults to the last scraped ID.")
    parser.add_argument('--end', type=int, default=2000000, help="The question ID to end scraping at.")
    
    args = parser.parse_args()

    last_scraped_id = get_last_scraped_id()
    start_id = args.start if args.start is not None else last_scraped_id + 1
    
    scrape_stackoverflow(start_id, args.end)

if __name__ == '__main__':
    main() 