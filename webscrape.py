import requests
from bs4 import BeautifulSoup
import re
import os
from urllib.parse import urljoin, urlparse
import time

def get_all_links(base_url):
    """Get all internal links from the website"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        links = set()
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Only include internal links from the same domain
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                links.add(full_url)
        
        return links
        
    except Exception as e:
        print(f"Error getting links: {e}")
        return set()

def scrape_page(url):
    """Scrape a single page"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
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

def scrape_entire_website():
    base_url = "https://www.freedomracing.com/"
    output_dir = "freedomracingdata"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all links
    print("Discovering all pages...")
    all_links = get_all_links(base_url)
    print(f"Found {len(all_links)} pages to scrape")
    
    scraped_count = 0
    for url in all_links:
        print(f"Scraping: {url}")
        
        # Scrape the page
        content = scrape_page(url)
        
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
            
            scraped_count += 1
            print(f"Saved: {filename}")
        
        # Be respectful to the server
        time.sleep(1)
    
    print(f"Scraping complete! Scraped {scraped_count} pages")

if __name__ == "__main__":
    scrape_entire_website()