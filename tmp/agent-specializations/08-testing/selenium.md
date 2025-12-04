---
name: selenium
type: testing
priority: 2
token_estimate: 400
compatible_with: [developer, senior_software_engineer, qa_expert]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Selenium WebDriver Expertise

## Specialist Profile
Selenium specialist building browser automation. Expert in WebDriver, waits, and cross-browser testing patterns.

## Implementation Guidelines

### Page Object Model

```python
# pages/base_page.py
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

    def find_element(self, locator):
        return self.wait.until(EC.presence_of_element_located(locator))

    def find_clickable(self, locator):
        return self.wait.until(EC.element_to_be_clickable(locator))

    def find_elements(self, locator):
        return self.wait.until(EC.presence_of_all_elements_located(locator))

# pages/users_page.py
from selenium.webdriver.common.by import By

class UsersPage(BasePage):
    # Locators
    USERS_LIST = (By.CSS_SELECTOR, "[data-testid='users-list']")
    USER_CARDS = (By.CSS_SELECTOR, "[data-testid='user-card']")
    CREATE_BUTTON = (By.XPATH, "//button[contains(text(), 'Create User')]")
    EMAIL_INPUT = (By.ID, "email")
    NAME_INPUT = (By.ID, "displayName")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    SUCCESS_TOAST = (By.CSS_SELECTOR, "[role='alert']")

    def __init__(self, driver):
        super().__init__(driver)
        self.url = "/users"

    def navigate(self):
        self.driver.get(f"{self.base_url}{self.url}")
        self.find_element(self.USERS_LIST)
        return self

    def get_user_count(self):
        return len(self.find_elements(self.USER_CARDS))

    def click_create_user(self):
        self.find_clickable(self.CREATE_BUTTON).click()
        return self

    def fill_user_form(self, email, display_name):
        self.find_element(self.EMAIL_INPUT).send_keys(email)
        self.find_element(self.NAME_INPUT).send_keys(display_name)
        return self

    def submit_form(self):
        self.find_clickable(self.SUBMIT_BUTTON).click()
        return self

    def get_success_message(self):
        return self.find_element(self.SUCCESS_TOAST).text
```

### Test Cases

```python
# tests/test_users.py
import pytest
from pages.users_page import UsersPage

class TestUsers:
    @pytest.fixture(autouse=True)
    def setup(self, driver):
        self.page = UsersPage(driver)
        self.page.navigate()

    def test_display_users_list(self):
        assert self.page.get_user_count() > 0

    def test_create_user(self):
        initial_count = self.page.get_user_count()

        self.page.click_create_user()
        self.page.fill_user_form("test@example.com", "Test User")
        self.page.submit_form()

        assert "Success" in self.page.get_success_message()
        assert self.page.get_user_count() == initial_count + 1

    def test_create_user_validation(self):
        self.page.click_create_user()
        self.page.fill_user_form("invalid-email", "")
        self.page.submit_form()

        # Should show validation errors
        error = self.page.find_element((By.CSS_SELECTOR, ".error-message"))
        assert "valid email" in error.text.lower()
```

### WebDriver Setup

```python
# conftest.py
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

@pytest.fixture(scope="session")
def driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)

    yield driver

    driver.quit()

@pytest.fixture(autouse=True)
def clean_state(driver):
    yield
    driver.delete_all_cookies()
```

### Wait Strategies

```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Explicit wait (preferred)
element = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "submit"))
)

# Custom wait condition
def element_has_text(locator, text):
    def check(driver):
        element = driver.find_element(*locator)
        return text in element.text
    return check

WebDriverWait(driver, 10).until(element_has_text((By.ID, "status"), "Complete"))

# Fluent wait
wait = WebDriverWait(driver, 30, poll_frequency=0.5,
                     ignored_exceptions=[StaleElementReferenceException])
```

## Patterns to Avoid
- ❌ time.sleep() for waits
- ❌ Hard-coded XPath selectors
- ❌ Not using Page Object Model
- ❌ Missing explicit waits

## Verification Checklist
- [ ] Page Object Model
- [ ] Explicit waits
- [ ] Data-testid selectors
- [ ] Cross-browser testing
- [ ] Headless mode support
