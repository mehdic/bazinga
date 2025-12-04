---
name: selenium
type: testing
priority: 2
token_estimate: 500
compatible_with: [developer, senior_software_engineer, qa_expert]
requires: []
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Selenium WebDriver Expertise

## Specialist Profile
Selenium specialist building browser automation. Expert in WebDriver, waits, and cross-browser testing patterns.

---

## Patterns to Follow

### Page Object Model
- **One class per page**: Encapsulate all locators/actions
- **Return self for chaining**: Fluent interface
- **Locators as class constants**: Easy to update
- **Methods for user actions**: Not low-level operations
- **Base page class**: Shared wait and navigation logic

### Wait Strategies
- **Explicit waits preferred**: `WebDriverWait` with conditions
- **Expected conditions**: `element_to_be_clickable`, `visibility_of`
- **Custom conditions**: For complex scenarios
- **Fluent waits**: Polling with ignored exceptions
- **Never use time.sleep()**: Always explicit

### Locator Strategy (Priority)
1. **data-testid**: Most stable
2. **ID**: If unique and stable
3. **name attribute**: Forms
4. **CSS selector**: Efficient, readable
5. **XPath**: Last resort for complex traversal

### Test Organization
- **pytest/JUnit fixtures**: Setup/teardown
- **Parameterized tests**: Multiple data sets
- **Parallel execution**: pytest-xdist, TestNG parallel
- **Screenshots on failure**: Debugging artifacts
- **Headless for CI**: Faster, no display needed

### Cross-Browser Testing
- **WebDriver Manager**: Auto-download drivers
- **Selenium Grid**: Parallel cross-browser
- **Cloud providers**: BrowserStack, SauceLabs
- **Configuration via fixtures**: Browser selection

### Selenium Version Features
<!-- version: selenium >= 4.0 -->
- **BiDi protocol**: Bidirectional WebDriver
- **Relative locators**: `above()`, `below()`, `near()`
- **New actions API**: Improved keyboard/mouse actions
- **Grid 4**: New architecture, Docker support
<!-- version: selenium >= 4.6 -->
- **Selenium Manager**: Built-in driver management
<!-- version: selenium >= 4.11 -->
- **Chrome DevTools Protocol**: CDP over BiDi
<!-- version: selenium < 4.0 -->
- **Selenium 3.x**: Requires explicit driver management

---

## Patterns to Avoid

### Wait Anti-Patterns
- ❌ **time.sleep()**: Unreliable, slow
- ❌ **Implicit waits globally**: Unpredictable
- ❌ **Mixing implicit/explicit**: Conflicts
- ❌ **Too short timeouts**: Flaky tests

### Locator Anti-Patterns
- ❌ **Absolute XPath**: `/html/body/div[3]/...` breaks easily
- ❌ **Auto-generated IDs**: Change between builds
- ❌ **CSS class names**: Styling changes break tests
- ❌ **Index-based locators**: Fragile to reordering

### Structure Anti-Patterns
- ❌ **No Page Object Model**: Duplicate locators everywhere
- ❌ **Test logic in page objects**: Keep pure
- ❌ **Giant test methods**: Split into focused tests
- ❌ **Shared browser state**: Tests affect each other

### Execution Anti-Patterns
- ❌ **No retry mechanism**: Flaky test failures
- ❌ **Missing artifacts**: Can't debug CI failures
- ❌ **Sequential only**: Slow feedback
- ❌ **No headless option**: CI environment issues

---

## Verification Checklist

### Structure
- [ ] Page Object Model implemented
- [ ] Base page with common methods
- [ ] Stable locator strategy
- [ ] Fixtures for setup/teardown

### Waits
- [ ] Explicit waits used
- [ ] No time.sleep()
- [ ] Custom conditions where needed
- [ ] Reasonable timeouts

### Execution
- [ ] Headless mode available
- [ ] Parallel test support
- [ ] Screenshots on failure
- [ ] Cross-browser configuration

### CI/CD
- [ ] WebDriver auto-management
- [ ] Artifacts uploaded
- [ ] Retry for flaky tests
- [ ] Grid or cloud integration

---

## Code Patterns (Reference)

### Page Object
- **Class**: `class UsersPage(BasePage): USERS_LIST = (By.CSS_SELECTOR, "[data-testid='users-list']")`
- **Method**: `def click_create(self): self.find_clickable(self.CREATE_BUTTON).click(); return self`
- **Wait**: `self.wait.until(EC.element_to_be_clickable(locator))`

### Explicit Wait
- **Standard**: `WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "result")))`
- **Custom**: `WebDriverWait(driver, 10).until(lambda d: "complete" in d.find_element(By.ID, "status").text)`
- **Fluent**: `WebDriverWait(driver, 30, poll_frequency=0.5, ignored_exceptions=[StaleElementReferenceException])`

### Fixtures (pytest)
- **Driver**: `@pytest.fixture(scope="session") def driver(): return webdriver.Chrome(options=Options().add_argument("--headless"))`
- **Cleanup**: `yield driver; driver.quit()`

### Test
- **Structure**: `def test_create_user(self, driver): page = UsersPage(driver).navigate(); page.click_create().fill_form(...).submit(); assert "Success" in page.get_message()`

