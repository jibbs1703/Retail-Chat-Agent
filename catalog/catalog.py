""" "Web Scraper Module for Sample Catalog Data."""

import asyncio
import json
import logging
import os
import re
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm

logging.basicConfig(level=logging.INFO, format="%(message)s")

logger = logging.getLogger("fashionnova_scraper")


class S3Connection:
    pass


class WebScraper:
    def __init__(self, request_delay, session, semaphore):
        self.request_delay = request_delay
        self.session = session
        self.semaphore = semaphore

    async def _fetch(self, url):
        """Internal helper to fetch page content with rate limiting."""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        async with self.semaphore:
            await asyncio.sleep(self.request_delay)
            try:
                async with self.session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        return await response.text()
                    return None
            except aiohttp.ClientError as e:
                logger.error(f"Error fetching {url}: {e}")
                return None

    def _parse_product_data(self, html, url):
        """Synchronous parsing logic (BeautifulSoup is not async)."""
        soup = BeautifulSoup(html, "html.parser")

        title = soup.title.string if soup.title else "No title found"
        price_node = soup.find("div", class_="text-red-600")
        price = price_node.get_text(strip=True) if price_node else "No price found"

        images = soup.select('div[data-testid^="product-image-"] picture img')
        img_urls = []
        for img in images:
            u = img.get("src") or (
                img.get("srcset", "").split(",")[0].strip().split(" ")[0]
                if img.get("srcset")
                else None
            )
            if u:
                img_urls.append(u.replace("&amp;", "&").split("?")[0])

        seen_imgs = set()
        unique_imgs = [u for u in img_urls if not (u in seen_imgs or seen_imgs.add(u))]

        product_details = []
        details_container = soup.select_one('[data-testid="product-details-text"]')
        if details_container:
            li_items = details_container.select("li")
            product_details = (
                [li.get_text(strip=True) for li in li_items]
                if li_items
                else [
                    line
                    for line in details_container.get_text("\n", strip=True).split("\n")
                    if line
                ]
            )

        financing = {}
        fin_btn = soup.select_one('button[data-testid="financing-options"]')
        if fin_btn:
            raw = fin_btn.get_text(" ", strip=True)
            m_payments = re.search(r"\bor\s+(\d+)\s+payments?\b", raw, flags=re.I)
            m_amount = re.search(r"(£\s?\d+(?:\.\d{2})?)", raw)
            financing = {
                "raw_text": raw,
                "payments_count": int(m_payments.group(1)) if m_payments else None,
                "payment_amount": m_amount.group(1).replace("£ ", "£") if m_amount else None,
            }

        size_options = []
        size_container = soup.select_one('[data-testid="product-size-options"]')
        if size_container:
            for btn in size_container.select('button[data-testid^="item-"]'):
                text = btn.get_text(" ", strip=True)
                if text:
                    size_options.append(text.split()[-1])

        return {
            "Product Title": title,
            "Product Price": price,
            "Product Images": unique_imgs,
            "No. of Images": len(unique_imgs),
            "Product Details": product_details,
            "Financing": financing,
            "Promo Tagline": soup.select_one('[data-testid="product-tagline"]').get_text(
                " ", strip=True
            )
            if soup.select_one('[data-testid="product-tagline"]')
            else None,
            "Size Options": list(dict.fromkeys(size_options)),
            "Product URL": url,
        }

    async def scrape_product(self, url):
        """Orchestrates fetching and parsing a single product."""
        html = await self._fetch(url)
        if not html:
            return {"Product URL": url, "error": "Failed to retrieve page"}
        return self._parse_product_data(html, url)

    async def get_product_urls_from_collection(self, collection_url, limit=60):
        """Retrieves product links from a collection page."""
        html = await self._fetch(collection_url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        urls = []
        for a in soup.select('a[href^="/products/"]'):
            href = a.get("href")
            if href:
                full = urljoin(collection_url, href)
                urls.append(urlparse(full)._replace(query="", fragment="").geturl())

        return list(dict.fromkeys(urls))[:limit]


async def scrape(  # noqa: C901
    concurrent_requests: int = 10,
    categories: tuple[str, ...] = ("shoes", "bodysuits", "jackets"),
    number_of_pages: int = 3,
    limit_per_page: int = 60,
    save_local: bool = False,
    output_dir: str = "catalog",
) -> None:
    """Main orchestration function for scraping Product catalog."""
    os.makedirs(output_dir, exist_ok=True)
    sem = asyncio.Semaphore(concurrent_requests)

    async with aiohttp.ClientSession() as session:
        scraper = WebScraper(request_delay=1.0, session=session, semaphore=sem)

        collection_tasks = []
        for category in categories:
            for page in range(1, number_of_pages + 1):
                url = (
                    f"https://www.fashionnova.com/collections/{category}?division=women&page={page}"
                )
                collection_tasks.append((category, url))

        logger.info(f"Gathering product URLs from {len(collection_tasks)} collection pages...")

        urls_by_category = {category: [] for category in categories}
        for category, url in collection_tasks:
            urls = await scraper.get_product_urls_from_collection(url, limit=limit_per_page)
            urls_by_category[category].extend(urls)

        for category in urls_by_category:
            urls_by_category[category] = list(dict.fromkeys(urls_by_category[category]))

        total_urls = sum(len(urls) for urls in urls_by_category.values())
        logger.info(f"Scraping {total_urls} products across {len(categories)} categories...")

        results_by_category = {category: [] for category in categories}

        for category in categories:
            if not urls_by_category[category]:
                logger.info(f"No products found for category: {category}")
                continue
            tasks = [scraper.scrape_product(url) for url in urls_by_category[category]]
            for progress in tqdm.as_completed(
                tasks, total=len(tasks), desc=f"Scraping {category.title()}"
            ):
                result = await progress
                results_by_category[category].append(result)

        if save_local:
            for category in categories:
                if results_by_category[category]:
                    output_file = f"{output_dir}/{category}_catalog.json"
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(results_by_category[category], f, ensure_ascii=False, indent=2)

                    success_count = sum(
                        1 for result in results_by_category[category] if "error" not in result
                    )
                    logger.info(f"Saved {success_count} products to {output_file}")

            total_success = sum(
                sum(1 for result in results_by_category[cat] if "error" not in result)
                for cat in categories
            )
            logger.info(f"Finished. Total products successfully scraped: {total_success}")
        else:
            logger.info("Scraping completed. Results not saved locally as per configuration.")
            # TODO: Implement S3 saving logic here.


if __name__ == "__main__":
    asyncio.run(scrape())
