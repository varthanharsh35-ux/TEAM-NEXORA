"""Standard-library HTTP fetcher respecting robots.txt and conditional GET."""

import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser


class Fetcher:
    """Polite HTTP fetcher with robots.txt compliance and ETag caching."""

    def __init__(self, base_url: str, agent: str = "GramSahayak-SIH26091/2.0"):
        self.base_url = base_url.rstrip("/")
        self.agent = agent
        self.rp = urllib.robotparser.RobotFileParser()
        self.crawl_delay = 0
        self.last_fetch = 0.0
        self._robots_loaded = False

    def parse_robots_txt(self, lines: list[str]):
        """Parse robots.txt lines and extract crawl-delay."""
        self.rp.parse(lines)
        delay = self.rp.crawl_delay(self.agent)
        if delay:
            self.crawl_delay = int(delay)
        self._robots_loaded = True

    def check_robots(self, path: str = "/") -> bool:
        """Parse robots.txt and verify permission for the configured user-agent."""
        robots_url = f"{self.base_url}/robots.txt"
        if not self._robots_loaded:
            try:
                req = urllib.request.Request(robots_url, headers={"User-Agent": self.agent})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    lines = resp.read().decode("utf-8", errors="ignore").splitlines()
                    self.parse_robots_txt(lines)
            except Exception:
                # If robots.txt is missing (404) or fails, default allow per standard
                self.rp.allow_all = True
                self._robots_loaded = True

        full_url = urllib.parse.urljoin(self.base_url + "/", path.lstrip("/"))
        return bool(self.rp.can_fetch(self.agent, full_url))

    def get(self, path: str, etag: str = None) -> tuple[int, bytes | None, str | None]:
        """Perform conditional GET (status, body, new_etag). Respects crawl-delay."""
        full_url = urllib.parse.urljoin(self.base_url + "/", path.lstrip("/"))

        if not self.check_robots(path):
            raise ValueError(f"robots_disallowed: {full_url}")

        if self.crawl_delay > 0:
            elapsed = time.monotonic() - self.last_fetch
            if elapsed < self.crawl_delay:
                time.sleep(self.crawl_delay - elapsed)

        headers = {"User-Agent": self.agent}
        if etag:
            headers["If-None-Match"] = etag

        req = urllib.request.Request(full_url, headers=headers)
        try:
            self.last_fetch = time.monotonic()
            with urllib.request.urlopen(req, timeout=15) as resp:
                status = resp.status
                body = resp.read()
                new_etag = resp.headers.get("ETag")
                return status, body, new_etag
        except urllib.error.HTTPError as e:
            self.last_fetch = time.monotonic()
            if e.code == 304:
                return 304, None, etag
            raise
        except Exception:
            self.last_fetch = time.monotonic()
            raise


if __name__ == "__main__":
    import io

    # 1. Test robot parser disallow rule
    f1 = Fetcher("https://example.gov.in", agent="GramSahayak-SIH26091/2.0")
    f1.parse_robots_txt([
        "User-agent: *",
        "Disallow: /private",
        "Crawl-delay: 2"
    ])
    assert f1.check_robots("/public") is True
    assert f1.check_robots("/private") is False

    # 2. ValueError raised on disallowed path
    try:
        f1.get("/private")
        assert False, "Should raise ValueError when robots disallows"
    except ValueError as e:
        assert "robots_disallowed" in str(e)

    # 3. Test allowed path check
    f2 = Fetcher("https://opendata.gov.in")
    f2.parse_robots_txt([
        "User-agent: *",
        "Allow: /"
    ])
    assert f2.check_robots("/dataset/schemes") is True

    # 4. Crawl delay extraction
    assert f1.crawl_delay == 2

    # 5. Fetcher initialization defaults
    f3 = Fetcher("https://test.gov.in")
    assert f3.agent == "GramSahayak-SIH26091/2.0"
    assert f3.base_url == "https://test.gov.in"

    print("All 5+ fetcher tests passed successfully!")
