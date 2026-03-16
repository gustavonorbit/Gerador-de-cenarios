from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class DriverHelper:
    """Tiny helper to start/stop chromedriver service for Robot tests.

    Usage from Robot:
        ${remote}=    Start Chromedriver    headless=False
        Open Browser    about:blank    chrome    remote_url=${remote}
        ...
        Stop Chromedriver
    """

    def __init__(self):
        self._service = None

    def start_chromedriver(self, headless: bool = False) -> str:
        """Download chromedriver (if needed) and start the service.

        Returns the service URL to be used as `remote_url` in SeleniumLibrary.
        """
        path = ChromeDriverManager().install()
        options = webdriver.ChromeOptions()
        if headless:
            # Use non-headless by default; allow headless when requested
            options.add_argument("--headless=new")
        # Prevent automatic browser closure by Robot — caller will close browsers
        service = Service(executable_path=path)
        service.start()
        self._service = service
        # service.service_url typically like http://127.0.0.1:9515
        return service.service_url

    def stop_chromedriver(self) -> None:
        if self._service:
            try:
                self._service.stop()
            except Exception:
                pass
            self._service = None


# Module-level helper instance and function wrappers so Robot can import
# the Python file as a library and find keywords like 'Start Chromedriver'.
_helper = DriverHelper()

def start_chromedriver(headless: bool = False) -> str:
    return _helper.start_chromedriver(headless=headless)


def stop_chromedriver() -> None:
    return _helper.stop_chromedriver()


def create_chrome_driver(show_ui: bool = True):
    """Start chromedriver service and create a Chrome WebDriver.

    Returns the `selenium.webdriver.Chrome` instance which can be passed
    to SeleniumLibrary's `Register Driver` keyword.
    """
    # normalize boolean
    s = show_ui
    try:
        # if passed as string
        if isinstance(show_ui, str):
            s = show_ui.lower() in ("1", "true", "yes")
    except Exception:
        s = bool(show_ui)

    path = ChromeDriverManager().install()
    options = webdriver.ChromeOptions()
    if not s:
        # headless when SHOW_UI is False
        options.add_argument("--headless=new")
    service = Service(executable_path=path)
    # start service implicitly when creating driver
    driver = webdriver.Chrome(service=service, options=options)
    return driver
