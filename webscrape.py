import requests
from bs4 import BeautifulSoup
import re
import os
import csv
from urllib.parse import urljoin, urlparse
import time
from collections import Counter

def scrape_page(url):
    """Scrape a single page with more targeted content extraction"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove common header/footer/navigation elements
        for element in soup.find_all(['nav', 'header', 'footer']):
            element.decompose()
        
        # Remove dropdown menus
        for dropdown in soup.find_all('div', class_='dropdown-menu'):
            dropdown.decompose()
        
        # Remove common navigation/menu classes (customize based on your site)
        navigation_selectors = [
            '.navbar', '.nav-menu', '.header', '.footer', '.sidebar',
            '.breadcrumb', '.pagination', '.social-links', '.contact-info'
        ]
        for selector in navigation_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        # Target main content areas (customize based on your site structure)
        main_content_selectors = [
            'main', '.main-content', '.content', '.page-content', 
            '.article', '.post', '.product-info', '#content'
        ]
        
        main_content = None
        for selector in main_content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # If no main content found, fall back to body but exclude known repetitive elements
        if not main_content:
            main_content = soup.find('body')
            if main_content:
                # Remove additional repetitive elements
                for element in main_content.find_all(['script', 'style', 'head', 'title', 'meta']):
                    element.decompose()
        
        # Extract text from the main content area
        if main_content:
            all_text = []
            for element in main_content.find_all(string=True):
                text = element.strip()
                if text and element.parent.name not in ['script', 'style', 'head', 'title', 'meta']:
                    all_text.append(text)
            return all_text
        
        return None
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def identify_common_content(all_scraped_content, threshold=0.5):
    """Identify content that appears across multiple pages (likely header/footer)"""
    if len(all_scraped_content) < 2:
        return set()
    
    # Count occurrences of each text snippet across all pages
    text_counter = Counter()
    total_pages = len(all_scraped_content)
    
    for page_content in all_scraped_content:
        if page_content:
            unique_texts = set(page_content)  # Remove duplicates within same page
            for text in unique_texts:
                # Only consider substantial text (not single words or very short phrases)
                if len(text.strip()) > 10:
                    text_counter[text.strip()] += 1
    
    # Identify text that appears on more than threshold percentage of pages
    common_threshold = max(2, int(total_pages * threshold))
    common_content = {text for text, count in text_counter.items() if count >= common_threshold}
    
    return common_content

def clean_content(content, common_content=None):
    """Clean and format the content, removing common header/footer elements"""
    if not content:
        return ""
    
    page_lines = []
    
    for text in content:
        text = text.strip()
        
        # Skip empty lines
        if not text:
            continue
            
        # Skip common repetitive content if provided
        if common_content and text in common_content:
            continue
            
        # Skip very short text that's likely navigation
        if len(text) < 3:
            continue
            
        # Skip common navigation patterns
        nav_patterns = [
            r'^(Home|About|Contact|Products|Services|Blog|News)$',
            r'^(Login|Register|Sign In|Sign Up)$',
            r'^(Cart|Checkout|Account|Profile)$',
            r'^(\d+)$',  # Just numbers
            r'^[<>«»‹›]+$',  # Just navigation arrows
        ]
        
        skip_line = False
        for pattern in nav_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                skip_line = True
                break
        
        if skip_line:
            continue
            
        page_lines.append(text)
    
    page = "\n\n".join(page_lines)
    
    # Additional content-specific cleaning (customize for your site)
    
    # Find and remove content before main content indicators
    main_content_indicators = ["Register", "Welcome", "Products", "Home >"]
    for indicator in main_content_indicators:
        indicator_index = page.find(indicator)
        if indicator_index != -1:
            page = page[indicator_index:]
            break
    
    # Find and remove content after footer indicators
    footer_indicators = [
        "© 2023 Freedom Racing Tool and Auto, LLC. All Rights Reserved.",
        "Copyright", "All rights reserved", "Privacy Policy", "Terms of Service"
    ]
    for indicator in footer_indicators:
        footer_index = page.find(indicator)
        if footer_index != -1:
            page = page[:footer_index + len(indicator)]
            break
    
    # Clean up excessive whitespace
    page = re.sub(r'\n{3,}', '\n\n', page)
    page = re.sub(r'\n\n(\$\d+\.\d+)', r'\n\1', page)
    
    return page

def two_pass_scraping(base_url):
    """Two-pass approach: First pass identifies common content, second pass filters it out"""
    output_dir = "freedomracingdata_filtered"
    csv_filepath = os.path.join(output_dir, "discovered_links.csv")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # PASS 1: Discover all URLs and scrape content for analysis
    print("Pass 1: Discovering pages and analyzing common content...")
    
    to_visit = {base_url}
    visited = set()
    all_scraped_content = []
    url_content_map = {}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    base_domain = urlparse(base_url).netloc
    
    while to_visit and len(visited) < 50:  # Limit for analysis phase
        current_url = to_visit.pop()
        
        if current_url in visited:
            continue
            
        visited.add(current_url)
        print(f"Analyzing page {len(visited)}: {current_url}")
        
        try:
            # Scrape content
            content = scrape_page(current_url)
            if content:
                all_scraped_content.append(content)
                url_content_map[current_url] = content
            
            # Discover new links
            response = requests.get(current_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(current_url, href)
                parsed_url = urlparse(full_url)
                clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                
                if (parsed_url.netloc == base_domain and 
                    clean_url.startswith(base_url) and 
                    clean_url not in visited and
                    clean_url not in to_visit):
                    to_visit.add(clean_url)
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error in pass 1 for {current_url}: {e}")
    
    # Identify common content across pages
    print("\nIdentifying common header/footer content...")
    common_content = identify_common_content(all_scraped_content, threshold=0.4)
    print(f"Found {len(common_content)} common text elements to filter out")
    
    # PASS 2: Continue scraping with filtering
    print("\nPass 2: Scraping remaining pages with content filtering...")
    
    scraped_count = 0
    failed_count = 0
    
    # Process already scraped pages with filtering
    for url, content in url_content_map.items():
        cleaned_content = clean_content(content, common_content)
        if save_page_content(url, cleaned_content, output_dir, csv_filepath):
            scraped_count += 1
        else:
            failed_count += 1
    
    # Continue with remaining pages
    while to_visit:
        current_url = to_visit.pop()
        
        if current_url in visited:
            continue
            
        visited.add(current_url)
        print(f"Processing page {len(visited)}: {current_url}")
        
        try:
            content = scrape_page(current_url)
            if content:
                cleaned_content = clean_content(content, common_content)
                if save_page_content(current_url, cleaned_content, output_dir, csv_filepath):
                    scraped_count += 1
                else:
                    failed_count += 1
            
            # Continue discovering links
            response = requests.get(current_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(current_url, href)
                parsed_url = urlparse(full_url)
                clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                
                if (parsed_url.netloc == base_domain and 
                    clean_url.startswith(base_url) and 
                    clean_url not in visited and
                    clean_url not in to_visit):
                    to_visit.add(clean_url)
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error processing {current_url}: {e}")
            failed_count += 1
    
    print(f"\n{'='*50}")
    print(f"Filtered crawl complete!")
    print(f"Successfully scraped: {scraped_count} pages")
    print(f"Failed to scrape: {failed_count} pages")
    print(f"Total pages discovered: {len(visited)}")
    print(f"Content saved to: {output_dir}/")

def save_page_content(url, content, output_dir, csv_filepath):
    """Save page content and URL"""
    if content and content.strip():
        filename = url_to_filename(url)
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {url}\n\n")
            f.write(content)
        
        # Save URL to CSV
        save_url_to_csv(url, csv_filepath)
        
        print(f"✓ Saved: {filename}")
        return True
    else:
        print(f"✗ No content to save: {url}")
        return False

def url_to_filename(url):
    """Convert URL to valid filename"""
    filename = url.replace('https://', '').replace('http://', '')
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'_+', '_', filename)
    filename = filename.rstrip('._')
    return filename + '.md'

def save_url_to_csv(url, csv_filepath):
    """Save URL to CSV file"""
    file_exists = os.path.isfile(csv_filepath)
    
    with open(csv_filepath, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        if not file_exists:
            writer.writerow(['url'])
        
        writer.writerow([url])

if __name__ == "__main__":
    base_url = "https://www.freedomracing.com/"
    two_pass_scraping(base_url)