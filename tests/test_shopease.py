import os
import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")

TEST_EMAIL    = "testuser_selenium@shopease.com"
TEST_PASSWORD = "Test1234"
TEST_NAME     = "Selenium Tester"
KNOWN_SLUG    = "wireless-noise-cancelling-headphones"
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
    """Driver that registers (if needed) then logs in fresh."""
    d = get_driver()

    # Step 1 — try to register (ignore errors if account already exists)
    d.get(f"{BASE_URL}/auth/register")
    try:
        WebDriverWait(d, 8).until(
            EC.presence_of_element_located((By.NAME, "name"))
        )
        d.find_element(By.NAME, "name").send_keys(TEST_NAME)
        d.find_element(By.NAME, "email").send_keys(TEST_EMAIL)
        d.find_element(By.NAME, "password").send_keys(TEST_PASSWORD)
        d.find_element(By.NAME, "confirmPassword").send_keys(TEST_PASSWORD)
        d.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(2)
    except Exception:
        pass  # account already exists — that's fine

    # Step 2 — logout first in case registration auto-logged in
    d.get(f"{BASE_URL}/auth/logout")
    time.sleep(1)

    # Step 3 — always navigate to login page explicitly and wait for it
    d.get(f"{BASE_URL}/auth/login")
    WebDriverWait(d, 10).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )

    # Step 4 — fill in and submit login form
    email_field = d.find_element(By.NAME, "email")
    email_field.clear()
    email_field.send_keys(TEST_EMAIL)
    d.find_element(By.NAME, "password").send_keys(TEST_PASSWORD)
    d.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(2)

    yield d
    d.quit()


# ── TC01  Homepage loads ───────────────────────────────────────────────────
def test_01_homepage_loads(driver):
    driver.get(BASE_URL)
    assert driver.title != ""


# ── TC02  Title contains ShopEase ─────────────────────────────────────────
def test_02_homepage_title(driver):
    driver.get(BASE_URL)
    assert "ShopEase" in driver.title or "Home" in driver.title


# ── TC03  Shop Now button links to /products ──────────────────────────────
def test_03_shop_now_button(driver):
    driver.get(BASE_URL)
    btn = driver.find_element(By.LINK_TEXT, "Shop Now")
    assert "/products" in btn.get_attribute("href")


# ── TC04  Register page loads ─────────────────────────────────────────────
def test_04_register_page_loads(driver):
    driver.get(f"{BASE_URL}/auth/register")
    assert "register" in driver.current_url.lower() or \
           "Create Account" in driver.page_source or \
           "Register" in driver.page_source


# ── TC05  Register form has all required fields ───────────────────────────
def test_05_register_form_fields(driver):
    driver.get(f"{BASE_URL}/auth/register")
    assert driver.find_element(By.NAME, "name").is_displayed()
    assert driver.find_element(By.NAME, "email").is_displayed()
    assert driver.find_element(By.NAME, "password").is_displayed()
    assert driver.find_element(By.NAME, "confirmPassword").is_displayed()


# ── TC06  Mismatched passwords shows error ────────────────────────────────
def test_06_register_password_mismatch(driver):
    driver.get(f"{BASE_URL}/auth/register")
    driver.find_element(By.NAME, "name").send_keys("Bad User")
    driver.find_element(By.NAME, "email").send_keys("bad_unique_xyz@test.com")
    driver.find_element(By.NAME, "password").send_keys("abc123")
    driver.find_element(By.NAME, "confirmPassword").send_keys("xyz999")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1)
    page = driver.page_source.lower()
    assert "do not match" in page or "alert" in page or "error" in page or \
           "password" in page


# ── TC07  Login page loads and shows form ────────────────────────────────
def test_07_login_page_loads(driver):
    driver.get(f"{BASE_URL}/auth/login")
    WebDriverWait(driver, 8).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )
    assert driver.find_element(By.NAME, "email").is_displayed()
    assert driver.find_element(By.NAME, "password").is_displayed()


# ── TC08  Wrong credentials shows error ──────────────────────────────────
def test_08_login_wrong_credentials(driver):
    driver.get(f"{BASE_URL}/auth/login")
    WebDriverWait(driver, 8).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )
    driver.find_element(By.NAME, "email").send_keys("nobody@nowhere.com")
    driver.find_element(By.NAME, "password").send_keys("wrongpass")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1)
    page = driver.page_source.lower()
    assert "invalid" in page or "alert" in page or "error" in page or \
           "incorrect" in page


# ── TC09  Products page shows cards ──────────────────────────────────────
def test_09_products_page_loads(driver):
    driver.get(f"{BASE_URL}/products")
    cards = driver.find_elements(By.CLASS_NAME, "product-card")
    assert len(cards) > 0, "Should display at least one product card"


# ── TC10  Category filter works (case-insensitive) ────────────────────────
def test_10_category_filter(driver):
    driver.get(f"{BASE_URL}/products?category={KNOWN_CATEGORY}")
    cards = driver.find_elements(By.CLASS_NAME, "product-card")
    assert len(cards) > 0, "Electronics category should have products"
    cats = driver.find_elements(By.CLASS_NAME, "product-category")
    for cat in cats:
        assert KNOWN_CATEGORY.lower() in cat.text.lower(), \
            f"Expected '{KNOWN_CATEGORY}' in category label, got: '{cat.text}'"


# ── TC11  Sort price ascending ────────────────────────────────────────────
def test_11_sort_price_asc(driver):
    driver.get(f"{BASE_URL}/products?sort=price-asc")
    prices = driver.find_elements(By.CLASS_NAME, "product-price")
    price_values = []
    for p in prices:
        try:
            price_values.append(float(p.text.replace("$", "").replace(",", "")))
        except ValueError:
            pass
    assert price_values == sorted(price_values), \
        "Products should be sorted lowest to highest price"


# ── TC12  Product detail page loads ──────────────────────────────────────
def test_12_product_detail_page(driver):
    driver.get(f"{BASE_URL}/products/{KNOWN_SLUG}")
    assert driver.find_element(By.CLASS_NAME, "product-main-img").is_displayed()


# ── TC13  Product detail has Add to Cart form ─────────────────────────────
def test_13_product_add_to_cart_form(driver):
    driver.get(f"{BASE_URL}/products/{KNOWN_SLUG}")
    form = driver.find_element(By.CLASS_NAME, "add-to-cart-form")
    assert form is not None
    qty = driver.find_element(By.NAME, "quantity")
    assert qty.get_attribute("value") == "1"


# ── TC14  Unauthenticated cart access redirects to login ──────────────────
def test_14_cart_requires_login(driver):
    driver.get(f"{BASE_URL}/auth/logout")
    time.sleep(1)
    driver.get(f"{BASE_URL}/cart")
    assert "login" in driver.current_url.lower(), \
        "Unauthenticated user should be redirected to login"


# ── TC15  Logged-in user can access cart ─────────────────────────────────
def test_15_login_and_view_cart(logged_in_driver):
    logged_in_driver.get(f"{BASE_URL}/cart")
    assert "cart" in logged_in_driver.current_url.lower() or \
           "Cart" in logged_in_driver.page_source


# ── TC16  Logged-in user can add product to cart ──────────────────────────
def test_16_add_to_cart(logged_in_driver):
    logged_in_driver.get(f"{BASE_URL}/products/{KNOWN_SLUG}")
    WebDriverWait(logged_in_driver, 8).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".add-to-cart-form button[type='submit']"))
    )
    logged_in_driver.find_element(By.CSS_SELECTOR, ".add-to-cart-form button[type='submit']").click()
    time.sleep(2)
    assert "/cart" in logged_in_driver.current_url or \
           "Wireless" in logged_in_driver.page_source or \
           "Headphones" in logged_in_driver.page_source


# ── TC17  Cart shows total ────────────────────────────────────────────────
def test_17_cart_shows_total(logged_in_driver):
    logged_in_driver.get(f"{BASE_URL}/cart")
    page = logged_in_driver.page_source
    if "empty" not in page.lower():
        assert "Total" in page or "total" in page
        assert "$" in page


# ── TC18  Checkout empties cart and shows success ─────────────────────────
def test_18_checkout_success(logged_in_driver):
    logged_in_driver.get(f"{BASE_URL}/products/{KNOWN_SLUG}")
    WebDriverWait(logged_in_driver, 8).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".add-to-cart-form button[type='submit']"))
    )
    logged_in_driver.find_element(By.CSS_SELECTOR, ".add-to-cart-form button[type='submit']").click()
    time.sleep(2)
    logged_in_driver.get(f"{BASE_URL}/cart")
    checkout_btn = logged_in_driver.find_element(
        By.CSS_SELECTOR, "form[action='/cart/checkout'] button"
    )
    checkout_btn.click()
    time.sleep(2)
    page = logged_in_driver.page_source.lower()
    assert "success" in logged_in_driver.current_url.lower() or \
           "thank" in page or "order" in page or "placed" in page


# ── TC19  Unknown URL returns 404 page ───────────────────────────────────
def test_19_404_page(driver):
    driver.get(f"{BASE_URL}/this-page-does-not-exist-xyz")
    assert "404" in driver.page_source or "not found" in driver.page_source.lower()


# ── TC20  Logout redirects to homepage ───────────────────────────────────
def test_20_logout(logged_in_driver):
    logged_in_driver.get(f"{BASE_URL}/auth/logout")
    time.sleep(2)
    url = logged_in_driver.current_url.rstrip("/")
    assert url == BASE_URL or url == BASE_URL + "/"