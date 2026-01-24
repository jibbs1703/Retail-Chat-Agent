"""Simple Test DAG for Airflow Setup Verification."""

from datetime import datetime

from airflow.sdk import dag, task


@dag(
    dag_id='sample_hello_etl_dag',
    description='Simple test DAG to verify Airflow Setup',
    schedule='0/15 * * * *', # Every 15 minutes
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['managed'],
)
def hello_etl():
    """Simple ETL DAG using TaskFlow API."""

    @task
    def extract() -> str:
        """Extract task that returns a greeting."""
        message = "Hello Extract"
        print(message)
        return message
    
    @task
    def transform(data: str) -> str:
        """Transform task that modifies the extracted data."""
        transformed_message = f"{data} - Transformed"
        print(transformed_message)
        return transformed_message

    @task
    def load(data: str) -> None:
        """Load task that prints the final message."""
        final_message = f"{data} - Loaded"
        print(final_message)

    extracted_data = extract()
    transformed_data = transform(extracted_data)
    load(transformed_data)


hello_etl()
