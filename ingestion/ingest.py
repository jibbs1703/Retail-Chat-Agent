"""Web Scraper Module for Retail Product Agent."""

import asyncio
import logging
from io import BytesIO
from urllib.parse import urljoin, urlparse

import aiohttp
import boto3
import psycopg2
from botocore.exceptions import ClientError
from bs4 import BeautifulSoup
from psycopg2.errors import ConnectionFailure
from psycopg2.extras import Json
from tqdm.asyncio import tqdm

from backend.app.v1.core.configurations import get_settings

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)
settings = get_settings()


class S3Connection:
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3', 
                                      aws_access_key_id=settings.aws_access_key_id,
                                      aws_secret_access_key=settings.aws_secret_access_key,
                                      region_name=settings.aws_region)

    async def upload_image_bytes(self, image_bytes, s3_key):
        """Uploads raw bytes to S3."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=image_bytes,
                ContentType='image/jpeg'
            ))
            return f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
        except ClientError as e:
            logger.error(f"S3 Upload Error: {e}")
            return None


class DatabaseConnection:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=settings.postgres_database,
            user=settings.postgres_user,
            password=settings.postgres_password,
            host=settings.postgres_host
        )
        self.cur = self.conn.cursor()

    def save_product(self, data, s3_urls):
        try:
            price = float(data["Product Price"].replace('$', '').replace(',', ''))
            query = """
            INSERT INTO products (
                product_title, product_url, product_price, 
                product_images, size_options, product_details, 
                financing, promo_tagline, image_count
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (product_url) DO UPDATE SET updated_at = CURRENT_TIMESTAMP;
            """
            self.cur.execute(query, (
                data["Product Title"], data["Product URL"], price,
                s3_urls, data["Size Options"], Json(data["Product Details"]),
                Json(data["Financing"]), data["Promo Tagline"], len(s3_urls)
            ))
            self.conn.commit()
        except ConnectionFailure as e:
            logger.error(f"DB Insert Error: {e}")
            self.conn.rollback()


class WebScraper:
    def __init__(self, request_delay, session, semaphore, s3_conn, db_conn):
        self.request_delay = request_delay
        self.session = session
        self.semaphore = semaphore
        self.s3 = s3_conn
        self.db = db_conn

    async def _fetch(self, url, return_bytes=False):
        async with self.semaphore:
            await asyncio.sleep(self.request_delay)
            try:
                async with self.session.get(url, timeout=30) as response:
                    if response.status == 200:
                        return await response.read() if return_bytes else await response.text()
                    return None
            except HTTPException as e:
                logger.error(f"Fetch error {url}: {e}")
                return None

    def _parse_product_data(self, html, url):
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string if soup.title else "No title"
        return {
            "Product Title": title,
            "Product Price": "$20.00", # Placeholder for your logic
            "Product Images": ["url1", "url2"], # Placeholder
            "Product Details": [],
            "Financing": {},
            "Size Options": [],
            "Promo Tagline": "",
            "Product URL": url
        }

    async def process_full_product(self, url, category):
        """Fetches, parses, uploads images to S3, and saves to DB."""
        html = await self._fetch(url)
        if not html: return

        data = self._parse_product_data(html, url)
        
        # Create S3 Folder Name
        folder_name = data["Product Title"].split('|')[0].strip().replace(' ', '-')
        
        s3_urls = []
        for i, img_url in enumerate(data["Product Images"]):
            img_data = await self._fetch(img_url, return_bytes=True)
            if img_data:
                s3_key = f"{category}/{folder_name}/img_{i}.jpg"
                s3_link = await self.s3.upload_image_bytes(img_data, s3_key)
                if s3_link: s3_urls.append(s3_link)

        self.db.save_product(data, s3_urls)


async def scrape(
    bucket_name: str,
    concurrent_requests: int = 5,
    categories: tuple[str, ...] = ("shoes",),
):
    sem = asyncio.Semaphore(concurrent_requests)
    s3_conn = S3Connection(bucket_name)
    db_conn = DatabaseConnection()

    async with aiohttp.ClientSession() as session:
        scraper = WebScraper(1.0, session, sem, s3_conn, db_conn)

        for category in categories:
            # 1. Get Product Links
            coll_url = f"https://www.fashionnova.com/collections/{category}"
            product_links = await scraper.get_product_urls_from_collection(coll_url)
            
            # 2. Process products as they come
            tasks = [scraper.process_full_product(link, category) for link in product_links]
            for f in tqdm.as_completed(tasks, desc=f"Processing {category}"):
                await f


if __name__ == "__main__":
    asyncio.run(scrape(bucket_name="your-s3-bucket"))
