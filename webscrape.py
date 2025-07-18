import requests
from bs4 import BeautifulSoup
import re
import os
import csv
from urllib.parse import urljoin, urlparse
import time

def scrape_page(url):
    """Scrape a single page"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove dropdown menus entirely
        for dropdown in soup.find_all('div', class_='dropdown-menu'):
            dropdown.decompose()
        
        # Get all text from the remaining page
        all_text = []
        for element in soup.find_all(string=True):
            text = element.strip()
            if text and element.parent.name not in ['script', 'style', 'head', 'title', 'meta']:
                all_text.append(text)
        
        return all_text
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def clean_content(content):
    """Clean and format the content"""
    page = ""
    for text in content:
        page += text + "\n\n"
    
    # Find and remove content before "Register"
    register_index = page.find("Register")
    if register_index != -1:
        page = page[register_index:]
    
    # Find and remove content after the copyright notice
    copyright_text = "© 2023 Freedom Racing Tool and Auto, LLC. All Rights Reserved."
    copyright_index = page.find(copyright_text)
    if copyright_index != -1:
        page = page[:copyright_index + len(copyright_text)]
    
    # Clean up excessive whitespace
    page = re.sub(r'\n{3,}', '\n\n', page)  # Replace 3+ newlines with 2
    page = re.sub(r'\n\n(\$\d+\.\d+)', r'\n\1', page)  # Remove extra newline before prices
    page = re.sub(r'\n\n(Purchase and earn)', r'\n\1', page)  # Remove extra newline before purchase text
    
    return page

def url_to_filename(url):
    """Convert URL to valid filename"""
    # Remove https:// and http://
    filename = url.replace('https://', '').replace('http://', '')
    # Replace invalid characters with underscores
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Replace multiple underscores with single
    filename = re.sub(r'_+', '_', filename)
    # Remove trailing dots and underscores
    filename = filename.rstrip('._')
    return filename + '.md'

def save_url_to_csv(url, csv_filepath):
    """Save URL to CSV file"""
    file_exists = os.path.isfile(csv_filepath)
    
    with open(csv_filepath, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header if file is new
        if not file_exists:
            writer.writerow(['url'])
        
        writer.writerow([url])

def save_page_content(url, content, output_dir):
    """Save page content to markdown file"""
    if content:
        # Clean the content
        cleaned_content = clean_content(content)
        
        # Create filename
        filename = url_to_filename(url)
        filepath = os.path.join(output_dir, filename)
        
        # Save to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {url}\n\n")
            f.write(cleaned_content)
        
        print(f"✓ Saved: {filename}")
        return True
    else:
        print(f"✗ Failed to save: {url}")
        return False

def discover_and_scrape_website(base_url):
    """Systematically discover and scrape website pages"""
    output_dir = "freedomracingdata"
    csv_filepath = os.path.join(output_dir, "discovered_links.csv")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize tracking sets and queue
    to_visit = {base_url}
    visited = set()
    scraped_count = 0
    failed_count = 0
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    base_domain = urlparse(base_url).netloc
    
    print("Starting systematic website crawl and scrape...")
    
    while to_visit:
        current_url = to_visit.pop()
        
        if current_url in visited:
            continue
            
        visited.add(current_url)
        print(f"\nProcessing page {len(visited)}: {current_url}")
        
        try:
            # Step 1: Scrape the current page
            content = scrape_page(current_url)
            
            # Step 2: Save the page content to markdown file
            if save_page_content(current_url, content, output_dir):
                scraped_count += 1
            else:
                failed_count += 1
            
            # Step 3: Save URL to CSV file
            save_url_to_csv(current_url, csv_filepath)
            
            # Step 4: Discover new links from this page for continued systematic search
            response = requests.get(current_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links on this page
            new_links_found = 0
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(current_url, href)
                
                # Clean the URL (remove fragments and query params)
                parsed_url = urlparse(full_url)
                clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                
                # Only include internal links from the same domain
                if (parsed_url.netloc == base_domain and 
                    clean_url.startswith(base_url) and 
                    clean_url not in visited and
                    clean_url not in to_visit):
                    
                    to_visit.add(clean_url)
                    new_links_found += 1
            
            print(f"   Found {new_links_found} new links to visit")
            print(f"   Queue size: {len(to_visit)}")
            
            # Be respectful to the server
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error processing {current_url}: {e}")
            failed_count += 1
            # Still save the URL to CSV even if scraping failed
            save_url_to_csv(current_url, csv_filepath)
            continue
    
    print(f"\n{'='*50}")
    print(f"Systematic crawl and scrape complete!")
    print(f"Successfully scraped: {scraped_count} pages")
    print(f"Failed to scrape: {failed_count} pages")
    print(f"Total pages discovered: {len(visited)}")
    print(f"All URLs saved to: {csv_filepath}")
    print(f"All content saved to: {output_dir}/")

if __name__ == "__main__":
    base_url = "https://www.freedomracing.com/"
    discover_and_scrape_website(base_url)