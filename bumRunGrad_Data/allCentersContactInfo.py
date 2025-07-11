import json
import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin
import urllib3

# Disable SSL warnings globally
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BumrungradScraper:
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        self.centers_data = []
        self.scraped_data = []
        self.session = requests.Session()
        
        # Set headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Disable SSL verification to avoid certificate issues
        self.session.verify = False
        
        # Suppress SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def load_centers_data(self):
        """Load centers data from JSON file"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                self.centers_data = json.load(file)
            print(f"✅ Loaded {len(self.centers_data)} centers from {self.json_file_path}")
        except FileNotFoundError:
            print(f"❌ Error: File {self.json_file_path} not found")
            return False
        except json.JSONDecodeError:
            print(f"❌ Error: Invalid JSON format in {self.json_file_path}")
            return False
        return True
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove HTML entities
        text = text.replace('&nbsp;', ' ')
        return text
    
    def extract_contact_info(self, soup):
        """Extract contact information from the contact section"""
        contact_info = {}
        
        # Find the contact section
        contact_section = soup.find('div', class_='contact__group')
        if not contact_section:
            return contact_info
        
        # Extract phone numbers
        phone_numbers = []
        phone_links = contact_section.find_all('a', href=re.compile(r'tel:'))
        for link in phone_links:
            phone_numbers.append(link.get_text(strip=True))
        
        # Extract all text content and organize it
        contact_text = contact_section.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in contact_text.split('\n') if line.strip()]
        
        # Extract hours from text
        hours_pattern = r'(\d{1,2}[:.]?\d{0,2})\s*[-–]\s*(\d{1,2}[:.]?\d{0,2})'
        hours_matches = re.findall(hours_pattern, contact_text)
        
        contact_info = {
            'phone_numbers': phone_numbers,
            'contact_text': lines,
            'hours': hours_matches
        }
        
        return contact_info
    
    def extract_service_hours(self, soup):
        """Extract service hours information"""
        service_hours = {}
        
        # Find service hours section
        service_sections = soup.find_all('div', class_='contact__group')
        for section in service_sections:
            headline = section.find('h4', class_='contact__group__headline__service')
            if headline:
                service_text = section.get_text(separator='\n', strip=True)
                lines = [line.strip() for line in service_text.split('\n') if line.strip()]
                
                # Extract hours with more flexible patterns
                hours_info = []
                for line in lines:
                    if any(time_word in line.lower() for time_word in ['am', 'pm', 'daily', 'hour', 'time']):
                        hours_info.append(line)
                
                service_hours = {
                    'service_text': lines,
                    'hours_info': hours_info
                }
                break
        
        return service_hours
    
    def extract_location(self, soup):
        """Extract location information"""
        location_info = {}
        
        # Find location section
        location_sections = soup.find_all('div', class_='contact__group')
        for section in location_sections:
            headline = section.find('h4', class_='contact__group__headline__location')
            if headline:
                location_text = section.get_text(separator='\n', strip=True)
                lines = [line.strip() for line in location_text.split('\n') if line.strip()]
                
                # Extract building and floor information
                building_info = []
                for line in lines:
                    if any(keyword in line.lower() for keyword in ['building', 'floor', 'wing', 'level']):
                        building_info.append(line)
                
                location_info = {
                    'location_text': lines,
                    'building_info': building_info
                }
                break
        
        return location_info
    
    def scrape_center_details(self, center):
        """Scrape details for a single center"""
        try:
            url = center['detail_url']
            print(f"🔍 Scraping: {center['name']} - {url}")
            
            # Add delay to be respectful to the server
            time.sleep(1)
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract information using the div class structure
            contact_info = self.extract_contact_info(soup)
            service_hours = self.extract_service_hours(soup)
            location_info = self.extract_location(soup)
            
            # Create the result object
            result = {
                'name': center['name'],
                'original_image_url': center['image_url'],
                'original_location': center['location'],
                'detail_url': center['detail_url'],
                'scraped_data': {
                    'contact_information': contact_info,
                    'service_hours': service_hours,
                    'location': location_info
                },
                'scraping_status': 'success',
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error for {center['name']}: {str(e)}")
            return {
                'name': center['name'],
                'detail_url': center['detail_url'],
                'scraping_status': 'error',
                'error_message': f"Network error: {str(e)}",
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            print(f"❌ Unexpected error for {center['name']}: {str(e)}")
            return {
                'name': center['name'],
                'detail_url': center['detail_url'],
                'scraping_status': 'error',
                'error_message': f"Unexpected error: {str(e)}",
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def scrape_all_centers(self):
        """Scrape all centers data"""
        print(f"🚀 Starting to scrape {len(self.centers_data)} centers...")
        
        for i, center in enumerate(self.centers_data, 1):
            print(f"\n📋 Progress: {i}/{len(self.centers_data)}")
            
            result = self.scrape_center_details(center)
            self.scraped_data.append(result)
            
            # Show progress
            if result['scraping_status'] == 'success':
                print(f"✅ Successfully scraped {center['name']}")
            else:
                print(f"❌ Failed to scrape {center['name']}")
        
        print(f"\n🎉 Scraping completed! Processed {len(self.scraped_data)} centers")
    
    def save_results(self, output_file='bumrungrad_centers_detailed.json'):
        """Save scraped results to JSON file"""
        try:
            # Create summary statistics
            successful_scrapes = sum(1 for item in self.scraped_data if item['scraping_status'] == 'success')
            failed_scrapes = len(self.scraped_data) - successful_scrapes
            
            final_data = {
                'scraping_summary': {
                    'total_centers': len(self.scraped_data),
                    'successful_scrapes': successful_scrapes,
                    'failed_scrapes': failed_scrapes,
                    'scraping_date': time.strftime('%Y-%m-%d %H:%M:%S')
                },
                'centers_data': self.scraped_data
            }
            
            with open(output_file, 'w', encoding='utf-8') as file:
                json.dump(final_data, file, ensure_ascii=False, indent=2)
            
            print(f"💾 Results saved to {output_file}")
            print(f"📊 Summary: {successful_scrapes} successful, {failed_scrapes} failed")
            
        except Exception as e:
            print(f"❌ Error saving results: {str(e)}")
    
    def run(self, output_file='bumrungrad_centers_detailed.json'):
        """Main method to run the scraper"""
        if not self.load_centers_data():
            return
        
        self.scrape_all_centers()
        self.save_results(output_file)

# Example usage
if __name__ == "__main__":
    # Initialize the scraper
    scraper = BumrungradScraper('firstAllCenters.json')
    
    # Run the scraper
    scraper.run('bumrungrad_centers_complete_data.json')
    
    # Optional: Print some results
    print("\n📋 Sample of scraped data:")
    if scraper.scraped_data:
        sample = scraper.scraped_data[0]
        print(f"Center: {sample['name']}")
        print(f"Status: {sample['scraping_status']}")
        if sample['scraping_status'] == 'success':
            contact = sample['scraped_data']['contact_information']
            if contact.get('phone_numbers'):
                print(f"Phone numbers: {contact['phone_numbers']}")