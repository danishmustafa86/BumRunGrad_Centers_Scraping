from bs4 import BeautifulSoup
import json

# Load HTML from file
with open("bumrungrad_playwright.html", "r", encoding="utf-8") as file:
    html = file.read()

soup = BeautifulSoup(html, "html.parser")

base_url = "https://www.bumrungrad.com"
cards = soup.select(".col-sm-12.col-lg-6")

centers_data = []

for card in cards:
    # Extract name
    name_tag = card.select_one(".cardclinic-title strong")
    name = name_tag.get_text(strip=True) if name_tag else "N/A"

    # Extract image URL
    image_div = card.select_one(".icon-center")
    image_style = image_div['style'] if image_div else ""
    image_url = (
        base_url + image_style.split("url(")[-1].split(")")[0]
        if "url(" in image_style else "N/A"
    )

    # Extract location (cleaned text)
    location_div = card.select_one(".collapse > div")
    location = location_div.get_text(separator=' ', strip=True) if location_div else "N/A"

    # Extract detail page link
    detail_link = card.select_one(".collapse a")
    href = detail_link['href'] if detail_link else ""
    detail_url = href if href.startswith("http") else base_url + href

    # Clean up duplicates in URLs
    detail_url = detail_url.replace("https://www.bumrungrad.comhttps://", "https://")

    # Append to list
    centers_data.append({
        "name": name,
        "image_url": image_url,
        "location": location,
        "detail_url": detail_url
    })

# Save to JSON file
with open("centers.json", "w", encoding="utf-8") as f:
    json.dump(centers_data, f, indent=2, ensure_ascii=False)

print("✅ Clinic/center data saved to 'centers.json'")
