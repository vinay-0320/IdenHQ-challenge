from playwright.sync_api import sync_playwright
import json
import os
import time

BASE_URL = "https://hiring.idenhq.com/"  # Change to actual URL
SESSION_FILE = "session.json"
USERNAME = "meti.vinayakumara@cmr.edu.in"  # Replace with actual credentials
PASSWORD = "v5U9swrH"

def is_user_logged_in(page):
    """Checks if the user is already logged in."""
    return page.locator("text=Sign out").is_visible()

def login(page):
    """Performs login if not already logged in."""
    if page.locator("#email").is_visible():
        print("Logging in...")
        page.fill("#email", USERNAME)
        page.fill("#password", PASSWORD)
        page.click("button[type='submit']")
        page.wait_for_selector("text=Sign out", timeout=60000)
        print("Login successful!")
    else:
        print("Already logged in.")

def navigate_to_product_table(page):
    """Navigates to the product inventory page."""
    page.wait_for_selector("button:has-text('Launch Challenge')", timeout=60000)
    page.click("button:has-text('Launch Challenge')")
    page.wait_for_selector("text=Product Inventory", timeout=60000)
    page.click("text=Product Inventory")
    page.wait_for_selector("text=Showing", timeout=60000)

def scroll_to_load_all_products(page):
    """Scrolls to the bottom of the page until all products are loaded."""
    last_count = 0
    max_attempts = 50  # Max scroll attempts to avoid infinite loop
    attempts = 0

    while attempts < max_attempts:
        # Wait for products to load
        page.wait_for_selector("div.rounded-lg.border.bg-card.text-card-foreground.shadow-sm", timeout=60000)

        # Count current product cards
        product_cards = page.locator("div.rounded-lg.border.bg-card.text-card-foreground.shadow-sm").all()
        total_products = len(product_cards)
        print(f"Loaded {total_products} products so far...")

        if total_products == last_count:
            print("All products loaded. Stopping scroll.")
            break  # Stop scrolling if no new products appear

        last_count = total_products  # Update last product count

        # Scroll down
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)  # Allow time for new products to load
        
        attempts += 1
    
    print(f"Final product count: {total_products}")

def extract_product_data(page):
    """Extracts product details after fully scrolling."""
    products = []
    product_cards = page.locator("div.rounded-lg.border.bg-card.text-card-foreground.shadow-sm").all()

    for idx, card in enumerate(product_cards):
        try:
            print(f"Extracting product {idx+1}...")

            name = card.locator("h3").inner_text()
            product_id = card.locator("text=ID:").inner_text().split(":")[-1].strip()
            last_updated = card.locator("text=Last Updated:").inner_text().split(":")[-1].strip()
            score = card.locator("text=Score:").inner_text().split(":")[-1].strip()
            price = card.locator("text=Price:").inner_text().split(":")[-1].strip()
            mass = card.locator("text=Mass (kg):").inner_text().split(":")[-1].strip()

            product = {
                "Name": name,
                "ID": product_id,
                "Last Updated": last_updated,
                "Score": score,
                "Price": price,
                "Mass (kg)": mass,
            }
            products.append(product)
        except Exception as e:
            print(f"Error extracting product {idx+1}: {e}")
            page.screenshot(path=f"error_product_{idx+1}.png")  # Screenshot for debugging

    return products

def save_data_to_json(product_data):
    """Saves extracted product data to JSON."""
    with open("product_data.json", "w") as file:
        json.dump(product_data, file, indent=4)

def main():
    """Main function to handle login, navigation, scrolling, and product extraction."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        
        if os.path.exists(SESSION_FILE):
            context.storage_state(path=SESSION_FILE)
        
        page = context.new_page()
        page.goto(BASE_URL, wait_until="load")
        
        if not is_user_logged_in(page):
            login(page)
            context.storage_state(path=SESSION_FILE)
        
        navigate_to_product_table(page)
        scroll_to_load_all_products(page)  # Scroll until all products load
        product_data = extract_product_data(page)  # Extract after full scrolling
        save_data_to_json(product_data)
        
        print(f"Extracted {len(product_data)} products successfully!")
        browser.close()

if __name__ == "__main__":
    main()
