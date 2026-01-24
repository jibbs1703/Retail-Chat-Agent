"""Database Health Check DAG - Verifies PostgreSQL and Qdrant are ready."""

import logging
import os
from datetime import datetime

import psycopg2
import requests
from airflow.sdk import dag, task

logger = logging.getLogger(__name__)


@dag(
    dag_id="database_health_check",
    description="Verifies PostgreSQL and Qdrant databases are up and ready for writes",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["health", "database", "infrastructure"],
    default_args={
        "owner": "data-team",
        "retries": 3,
        "retry_delay": 10,
    },
)
def database_health_check():  # noqa: C901
    """
    Database Health Check DAG.

    Verifies that both data stores are accessible and ready:
    1. PostgreSQL (relational-db) - Product metadata
    2. Qdrant (vector-db) - Vector embeddings
    """

    @task
    def check_postgres() -> dict:
        """
        Check PostgreSQL connection and verify tables exist.
        """
        host = os.getenv("POSTGRES_HOST", "relational-db")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USER")
        password = os.getenv("POSTGRES_PASSWORD")
        database = os.getenv("POSTGRES_DATABASE")

        print(f"Connecting to PostgreSQL at {host}:{port}/{database}...")

        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                dbname=database,
                connect_timeout=10,
            )
            cursor = conn.cursor()

            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✓ PostgreSQL connected: {version[:50]}...")

            required_tables = ["products", "product_images", "embeddings"]
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE';
            """)
            existing_tables = [row[0] for row in cursor.fetchall()]

            print(f"Existing tables: {existing_tables}")

            missing_tables = [t for t in required_tables if t not in existing_tables]
            if missing_tables:
                raise Exception(f"Missing required tables: {missing_tables}")

            print(f"✓ All required tables exist: {required_tables}")

            cursor.execute("SELECT COUNT(*) FROM products;")
            product_count = cursor.fetchone()[0]
            print(f"✓ Products table accessible, current count: {product_count}")

            cursor.close()
            conn.close()

            return {
                "status": "healthy",
                "host": host,
                "port": port,
                "database": database,
                "tables": existing_tables,
                "product_count": product_count,
            }

        except Exception as e:
            print(f"✗ PostgreSQL check failed: {e}")
            raise

    @task
    def check_qdrant() -> dict:
        """
        Check Qdrant connection and verify collections can be created.
        """
        qdrant_url = os.getenv("QDRANT_URL", "http://vector-db:6333")

        base_url = qdrant_url

        print(f"Connecting to Qdrant at {base_url}...")

        try:
            response = requests.get(f"{base_url}/readyz", timeout=10)
            if response.status_code != 200:
                raise Exception(f"Qdrant not ready: {response.status_code}")
            print("✓ Qdrant is ready")

            response = requests.get(f"{base_url}/", timeout=10)
            info = response.json()
            print(f"✓ Qdrant version: {info.get('version', 'unknown')}")

            response = requests.get(f"{base_url}/collections", timeout=10)
            collections_data = response.json()
            existing_collections = [
                c["name"] for c in collections_data.get("result", {}).get("collections", [])
            ]
            print(f"Existing collections: {existing_collections}")

            required_collections = {
                "product_images": {"vectors": {"size": 768, "distance": "Cosine"}},
                "product_text": {"vectors": {"size": 768, "distance": "Cosine"}},
            }

            for collection_name, config in required_collections.items():
                if collection_name not in existing_collections:
                    print(f"Creating collection: {collection_name}...")
                    response = requests.put(
                        f"{base_url}/collections/{collection_name}",
                        headers={"Content-Type": "application/json"},
                        json=config,
                        timeout=30,
                    )
                    if response.status_code not in [200, 201]:
                        raise Exception(f"Failed to create {collection_name}: {response.text}")
                    print(f"✓ Created collection: {collection_name}")
                else:
                    print(f"✓ Collection exists: {collection_name}")

            response = requests.get(f"{base_url}/collections", timeout=10)
            collection_result = response.json().get("result", {}).get("collections", [])
            final_collections = [c["name"] for c in collection_result]

            return {
                "status": "healthy",
                "url": base_url,
                "version": info.get("version", "unknown"),
                "collections": final_collections,
            }

        except Exception as e:
            print(f"✗ Qdrant check failed: {e}")
            raise

    @task
    def report_status(postgres_result: dict, qdrant_result: dict) -> dict:
        """
        Generate final health report.
        """
        print("\n" + "=" * 60)
        print("DATABASE HEALTH CHECK REPORT")
        print("=" * 60)

        print("\n[PostgreSQL]")
        print(f"  Status: {postgres_result['status']}")
        print(f"  Host: {postgres_result['host']}:{postgres_result['port']}")
        print(f"  Database: {postgres_result['database']}")
        print(f"  Tables: {', '.join(postgres_result['tables'])}")
        print(f"  Products: {postgres_result['product_count']}")

        print("\n[Qdrant]")
        print(f"  Status: {qdrant_result['status']}")
        print(f"  URL: {qdrant_result['url']}")
        print(f"  Version: {qdrant_result['version']}")
        print(f"  Collections: {', '.join(qdrant_result['collections'])}")

        all_healthy = (
            postgres_result["status"] == "healthy" and qdrant_result["status"] == "healthy"
        )

        print("\n" + "=" * 60)
        if all_healthy:
            print("✓ ALL DATABASES READY FOR WRITES")
        else:
            print("✗ SOME DATABASES ARE NOT READY")
        print("=" * 60 + "\n")

        return {
            "timestamp": datetime.now().isoformat(),
            "all_healthy": all_healthy,
            "postgres": postgres_result,
            "qdrant": qdrant_result,
        }

    postgres_status = check_postgres()
    qdrant_status = check_qdrant()
    report_status(postgres_status, qdrant_status)


database_health_check()
