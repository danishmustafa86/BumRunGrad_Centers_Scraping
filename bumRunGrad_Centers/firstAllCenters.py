import asyncio
from playwright.async_api import async_playwright

async def main():
    url = "https://www.bumrungrad.com/en/clinics-and-centers"

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Go to the page
        response = await page.goto(url)
        print("Status Code:", response.status)

        # Wait for the search box input to ensure full render
        await page.wait_for_selector("input.input-search")

        # Save full HTML
        html_content = await page.content()
        with open("bumrungrad_playwright.html", "w", encoding="utf-8") as file:
            file.write(html_content)
        print("HTML content saved to 'bumrungrad_playwright.html'")

        await browser.close()

# Run the async script
asyncio.run(main())
