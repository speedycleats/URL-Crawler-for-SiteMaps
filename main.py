# Import necessary libraries
import requests  # For sending HTTP requests
from bs4 import BeautifulSoup  # For parsing HTML content
from urllib.parse import urljoin, urlparse  # For building and cleaning URLs
from tqdm import tqdm  # For displaying a live progress bar
import time  # To add delay between requests
import os  # For working with file paths
from datetime import datetime  # For timestamped filenames

# Function to extract internal links from a webpage
def fetch_links(url, base_netloc):
    """
    Fetch all internal links from the provided URL.
    Only returns links that belong to the same domain.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Error fetching {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    links = set()

    # Loop through all <a> tags and extract hrefs
    for tag in soup.find_all("a", href=True):
        href = tag.get("href")
        full_url = urljoin(url, href)  # Converts relative URLs to absolute
        parsed = urlparse(full_url)

        # Only keep links from the same domain
        if parsed.netloc == base_netloc:
            cleaned_url = parsed.scheme + "://" + parsed.netloc + parsed.path
            links.add(cleaned_url)

    return links

# Function to recursively crawl internal pages starting from a base URL
def crawl_site(start_url):
    """
    Recursively crawl internal pages starting from the given URL.
    Only includes URLs that return a 200 OK response.
    """
    visited = set()        # All URLs already checked
    valid_links = set()    # Only the URLs with 200 OK status
    to_visit = [start_url] # Queue of URLs still to crawl
    base_netloc = urlparse(start_url).netloc

    with tqdm(total=0, unit="page", dynamic_ncols=True) as progress:
        while to_visit:
            current_url = to_visit.pop(0)

            if current_url in visited:
                continue  # Skip if already visited

            try:
                response = requests.get(current_url, timeout=10)
                response.raise_for_status()
                valid_links.add(current_url)  # Only store successful responses
            except requests.RequestException as e:
                print(f"❌ Error fetching {current_url}: {e}")
                visited.add(current_url)
                continue

            visited.add(current_url)
            progress.set_description(f"Crawling")
            progress.update(1)

            # Extract internal links from the current page
            links = fetch_links(current_url, base_netloc)

            # Add new links to the queue
            for link in links:
                if link not in visited and link not in to_visit:
                    to_visit.append(link)

            time.sleep(0.5)  # Be polite to servers

    return valid_links

# Main program entry point
if __name__ == "__main__":
    # Ask user for a starting URL
    main_url = input("Enter a full URL (include https://): ").strip()

    # Start crawling from that URL
    all_links = crawl_site(main_url)

    # Display results in terminal
    print(f"\n✅ Finished! Found {len(all_links)} total internal pages:\n")
    for link in all_links:
        print(link)

    # Create a timestamp for output file naming
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"crawler_output_{timestamp}.txt"
    output_path = os.path.join(os.getcwd(), output_filename)

    # Save results in Markdown-style .txt format
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(f"# Crawl Results\n\n")
        file.write(f"**Crawled URL:** {main_url}\n")
        file.write(f"\n**Total Pages Found:** {len(all_links)}\n\n")
        file.write("---\n\n")

        for link in sorted(all_links):
            file.write(f"- {link}\n")

    print(f"\n📁 Results saved to: {output_path}")
