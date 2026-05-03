import os
import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Read from environment variable (set in Jenkinsfile), fallback to localhost
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")

# A test account - register once, reuse across tests
TEST_EMAIL = "testuser_selenium@shopease.com"
TEST_PASSWORD = "Test1234"
TEST_NAME = "Selenium Tester"

# A known product slug from your seed data
KNOWN_SLUG = "wireless-noise-cancelling-headphones"
KNOWN_CATEGORY = "Electronics"


def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(6)
    return driver


@pytest.fixture(scope="session")
def driver():
    d = get_driver()
    yield d
    d.quit()


@pytest.fixture(scope="session")
def logged_in_driver():
    """Separate driver that starts already logged in."""
    d = get_driver()
    # Register the test user (may fail if already exists — that's fine)
    d.get(f"{BASE_URL}/auth/register")
    try:
        d.find_element(By.NAME, "name").send_keys(TEST_NAME)
        d.find_element(By.NAME, "email").send_keys(TEST_EMAIL)
        d.find_element(By.NAME, "password").send_keys(TEST_PASSWORD)
        d.find_element(By.NAME, "confirmPassword").send_keys(TEST_PASSWORD)
        d.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)
    except Exception:
        pass
    # Log in fresh
    d.get(f"{BASE_URL}/auth/login")
    d.find_element(By.NAME, "email").clear()
    d.find_element(By.NAME, "email").send_keys(TEST_EMAIL)
    d.find_element(By.NAME, "password").send_keys(TEST_PASSWORD)
    d.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1)
    yield d
    d.quit()


# ──────────────────────────────────────────
# TC01  Homepage loads
# ──────────────────────────────────────────
def test_01_homepage_loads(driver):
    driver.get(BASE_URL)
    assert driver.title != "", "Page title should not be empty"


# ──────────────────────────────────────────
# TC02  Homepage title contains ShopEase
# ──────────────────────────────────────────
def test_02_homepage_title(driver):
    driver.get(BASE_URL)
    assert "ShopEase" in driver.title or "Home" in driver.title, \
        f"Expected ShopEase in title, got: {driver.title}"


# ──────────────────────────────────────────
# TC03  Hero section 'Shop Now' button exists and links to /products
# ──────────────────────────────────────────
def test_03_shop_now_button(driver):
    driver.get(BASE_URL)
    btn = driver.find_element(By.LINK_TEXT, "Shop Now")
    assert "/products" in btn.get_attribute("href")


# ──────────────────────────────────────────
# TC04  Register page loads
# ──────────────────────────────────────────
def test_04_register_page_loads(driver):
    driver.get(f"{BASE_URL}/auth/register")
    assert "register" in driver.current_url.lower() or \
           "Create Account" in driver.page_source


# ──────────────────────────────────────────
# TC05  Register form has all required fields
# ──────────────────────────────────────────
def test_05_register_form_fields(driver):
    driver.get(f"{BASE_URL}/auth/register")
    assert driver.find_element(By.NAME, "name").is_displayed()
    assert driver.find_element(By.NAME, "email").is_displayed()
    assert driver.find_element(By.NAME, "password").is_displayed()
    assert driver.find_element(By.NAME, "confirmPassword").is_displayed()


# ──────────────────────────────────────────
# TC06  Register with mismatched passwords shows error
# ──────────────────────────────────────────
def test_06_register_password_mismatch(driver):
    driver.get(f"{BASE_URL}/auth/register")
    driver.find_element(By.NAME, "name").send_keys("Bad User")
    driver.find_element(By.NAME, "email").send_keys("bad@test.com")
    driver.find_element(By.NAME, "password").send_keys("abc123")
    driver.find_element(By.NAME, "confirmPassword").send_keys("xyz999")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    assert "do not match" in driver.page_source.lower() or \
           "alert" in driver.page_source.lower()


# ──────────────────────────────────────────
# TC07  Login page loads and shows form
# ──────────────────────────────────────────
def test_07_login_page_loads(driver):
    driver.get(f"{BASE_URL}/auth/login")
    assert driver.find_element(By.NAME, "email").is_displayed()
    assert driver.find_element(By.NAME, "password").is_displayed()


# ──────────────────────────────────────────
# TC08  Login with wrong credentials shows error
# ──────────────────────────────────────────
def test_08_login_wrong_credentials(driver):
    driver.get(f"{BASE_URL}/auth/login")
    driver.find_element(By.NAME, "email").send_keys("nobody@nowhere.com")
    driver.find_element(By.NAME, "password").send_keys("wrongpass")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    assert "invalid" in driver.page_source.lower() or \
           "alert" in driver.page_source.lower()


# ──────────────────────────────────────────
# TC09  Products page loads and shows items
# ──────────────────────────────────────────
def test_09_products_page_loads(driver):
    driver.get(f"{BASE_URL}/products")
    assert "Shop" in driver.title or "Product" in driver.page_source
    cards = driver.find_elements(By.CLASS_NAME, "product-card")
    assert len(cards) > 0, "Should display at least one product card"


# ──────────────────────────────────────────
# TC10  Category filter works (Electronics)
# ──────────────────────────────────────────
def test_10_category_filter(driver):
    driver.get(f"{BASE_URL}/products?category={KNOWN_CATEGORY}")
    cards = driver.find_elements(By.CLASS_NAME, "product-card")
    assert len(cards) > 0, "Electronics category should have products"
    # All visible category labels should say Electronics
    cats = driver.find_elements(By.CLASS_NAME, "product-category")
    for cat in cats:
        assert KNOWN_CATEGORY in cat.text


# ──────────────────────────────────────────
# TC11  Sort by price low to high works
# ──────────────────────────────────────────
def test_11_sort_price_asc(driver):
    driver.get(f"{BASE_URL}/products?sort=price-asc")
    prices = driver.find_elements(By.CLASS_NAME, "product-price")
    price_values = []
    for p in prices:
        try:
            price_values.append(float(p.text.replace("$", "")))
        except ValueError:
            pass
    assert price_values == sorted(price_values), \
        "Products should be sorted from lowest to highest price"


# ──────────────────────────────────────────
# TC12  Single product detail page loads
# ──────────────────────────────────────────
def test_12_product_detail_page(driver):
    driver.get(f"{BASE_URL}/products/{KNOWN_SLUG}")
    assert "Wireless" in driver.page_source or KNOWN_SLUG.replace("-", " ").title() in driver.page_source
    assert driver.find_element(By.CLASS_NAME, "product-main-img").is_displayed()


# ──────────────────────────────────────────
# TC13  Product detail page has Add to Cart form
# ──────────────────────────────────────────
def test_13_product_add_to_cart_form(driver):
    driver.get(f"{BASE_URL}/products/{KNOWN_SLUG}")
    form = driver.find_element(By.CLASS_NAME, "add-to-cart-form")
    assert form is not None
    qty = driver.find_element(By.NAME, "quantity")
    assert qty.get_attribute("value") == "1"


# ──────────────────────────────────────────
# TC14  Unauthenticated cart access redirects to login
# ──────────────────────────────────────────
def test_14_cart_requires_login(driver):
    # Ensure logged out
    driver.get(f"{BASE_URL}/auth/logout")
    time.sleep(1)
    driver.get(f"{BASE_URL}/cart")
    assert "login" in driver.current_url.lower(), \
        "Unauthenticated user should be redirected to login"


# ──────────────────────────────────────────
# TC15  Successful login and cart access
# ──────────────────────────────────────────
def test_15_login_and_view_cart(logged_in_driver):
    logged_in_driver.get(f"{BASE_URL}/cart")
    # Should not redirect away — either shows cart or empty cart message
    assert "cart" in logged_in_driver.current_url.lower() or \
           "Cart" in logged_in_driver.page_source, \
        "Logged-in user should be able to access the cart"


# ──────────────────────────────────────────
# TC16  Add product to cart (logged in)
# ──────────────────────────────────────────
def test_16_add_to_cart(logged_in_driver):
    logged_in_driver.get(f"{BASE_URL}/products/{KNOWN_SLUG}")
    logged_in_driver.find_element(By.CSS_SELECTOR, ".add-to-cart-form button[type='submit']").click()
    time.sleep(1)
    # Should land on /cart
    assert "/cart" in logged_in_driver.current_url
    assert "Wireless" in logged_in_driver.page_source or \
           "Headphones" in logged_in_driver.page_source


# ──────────────────────────────────────────
# TC17  Cart shows correct total row
# ──────────────────────────────────────────
def test_17_cart_shows_total(logged_in_driver):
    logged_in_driver.get(f"{BASE_URL}/cart")
    if "empty" not in logged_in_driver.page_source.lower():
        assert "Total" in logged_in_driver.page_source
        assert "$" in logged_in_driver.page_source


# ──────────────────────────────────────────
# TC18  Checkout empties cart and shows success page
# ──────────────────────────────────────────
def test_18_checkout_success(logged_in_driver):
    # Make sure cart has something first
    logged_in_driver.get(f"{BASE_URL}/products/{KNOWN_SLUG}")
    logged_in_driver.find_element(By.CSS_SELECTOR, ".add-to-cart-form button[type='submit']").click()
    time.sleep(1)
    logged_in_driver.get(f"{BASE_URL}/cart")
    checkout_btn = logged_in_driver.find_element(By.CSS_SELECTOR, "form[action='/cart/checkout'] button")
    checkout_btn.click()
    time.sleep(1)
    assert "success" in logged_in_driver.current_url.lower() or \
           "Thank" in logged_in_driver.page_source or \
           "order" in logged_in_driver.page_source.lower()


# ──────────────────────────────────────────
# TC19  404 page for unknown URL
# ──────────────────────────────────────────
def test_19_404_page(driver):
    driver.get(f"{BASE_URL}/this-page-does-not-exist-xyz")
    assert "404" in driver.page_source or \
           "not found" in driver.page_source.lower()


# ──────────────────────────────────────────
# TC20  Logout redirects to homepage
# ──────────────────────────────────────────
def test_20_logout(logged_in_driver):
    logged_in_driver.get(f"{BASE_URL}/auth/logout")
    time.sleep(1)
    assert logged_in_driver.current_url == f"{BASE_URL}/" or \
           logged_in_driver.current_url == BASE_URL + "/"
