from bs4 import BeautifulSoup
import requests
import re

# Define the target URL
url = "https://mekoclinic.com/surgery/nose-open-rhinoplasty/"
headers = {
    "User-Agent": "Mozilla/5.0"
}

# Request the webpage
response = requests.get(url, headers=headers)

# Parse with BeautifulSoup
soup = BeautifulSoup(response.content, "html.parser")

# Remove unwanted scripts, styles, and metadata
for tag in soup(["script", "style", "noscript", "iframe", "meta", "link"]):
    tag.decompose()

# Extract useful parts: headings, paragraphs, image alt text
headings = [tag.get_text(strip=True) for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])]
paragraphs = [tag.get_text(strip=True) for tag in soup.find_all('p')]
list_items = [tag.get_text(strip=True) for tag in soup.find_all('li')]
image_alts = [tag.get('alt', '') for tag in soup.find_all('img') if tag.get('alt')]

# Optional: Extract prices (if mentioned)
text = soup.get_text()
prices = re.findall(r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:฿|baht|THB)', text, re.IGNORECASE)

# Combine everything into a single HTML content block
html_content = "<html><body>"
html_content += "<h1>Meko Clinic - Nose Open Rhinoplasty</h1>"

html_content += "<h2>Headings</h2><ul>" + "".join([f"<li>{h}</li>" for h in headings]) + "</ul>"
html_content += "<h2>Paragraphs</h2><p>" + "</p><p>".join(paragraphs) + "</p>"
html_content += "<h2>List Items</h2><ul>" + "".join([f"<li>{li}</li>" for li in list_items]) + "</ul>"
html_content += "<h2>Image Descriptions</h2><ul>" + "".join([f"<li>{alt}</li>" for alt in image_alts]) + "</ul>"
if prices:
    html_content += "<h2>Prices</h2><ul>" + "".join([f"<li>{price}</li>" for price in prices]) + "</ul>"

html_content += "</body></html>"

# Save to file
with open("meko_clinic_rhinoplasty.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("✅ Data successfully scraped and saved to 'meko_clinic_rhinoplasty.html'")
