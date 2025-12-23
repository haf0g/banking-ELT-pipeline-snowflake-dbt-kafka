import os
import boto3
import snowflake.connector
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook

from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# -------- MinIO Config --------
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
BUCKET = os.getenv("MINIO_BUCKET")
LOCAL_DIR = os.getenv("MINIO_LOCAL_DIR", "/tmp/minio_downloads")

# -------- Snowflake Config --------
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_DB = os.getenv("SNOWFLAKE_DB")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")

TABLES = ["customers", "accounts", "transactions"]

# -------- Python Callables --------
def download_from_minio():
     # DEBUG: Check if variables are actually loading
    print(f"DEBUG: Endpoint: {MINIO_ENDPOINT}")
    print(f"DEBUG: Access Key exists: {bool(MINIO_ACCESS_KEY)}") 
    
    if not MINIO_ACCESS_KEY or not MINIO_SECRET_KEY:
        raise ValueError("MinIO Credentials are missing! Check your environment variables.")
    
     # This will show you exactly what Python "sees"
    print(f"DEBUG: Key: '{MINIO_ACCESS_KEY}' (Length: {len(MINIO_ACCESS_KEY)})")
    print(f"DEBUG: Secret: '{MINIO_SECRET_KEY[0]}***{MINIO_SECRET_KEY[-1]}' (Length: {len(MINIO_SECRET_KEY)})")
    
    
    os.makedirs(LOCAL_DIR, exist_ok=True)
    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY
    )
    local_files = {}
    for table in TABLES:
        prefix = f"{table}/"
        resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
        objects = resp.get("Contents", [])
        local_files[table] = []
        for obj in objects:
            key = obj["Key"]
            local_file = os.path.join(LOCAL_DIR, os.path.basename(key))
            s3.download_file(BUCKET, key, local_file)
            print(f"Downloaded {key} -> {local_file}")
            local_files[table].append(local_file)
    return local_files

def load_to_snowflake(**kwargs):
    local_files = kwargs["ti"].xcom_pull(task_ids="download_minio")
    
    if not local_files:
        print("Aucun fichier à charger.")
        return

    hook = SnowflakeHook(snowflake_conn_id="snowflake_default")
    conn = hook.get_conn()
    cur = conn.cursor()

    try:
        for table, files in local_files.items():
            for f in files:
                # 1. Upload file to stage
                cur.execute(f"PUT file://{f} @%{table} OVERWRITE=TRUE")
            
            # 2. THE FIX: Explicitly select $1 (the whole row) into column 'v'
            # We don't mention 'load_timestamp' because it has a DEFAULT value
            copy_sql = f"""
                COPY INTO {table} (v)
                FROM (
                    SELECT $1 
                    FROM @%{table}
                )
                FILE_FORMAT = (TYPE = PARQUET)
                ON_ERROR = 'CONTINUE'
            """
            cur.execute(copy_sql)
            print(f"✅ {table} chargé avec succès dans la colonne VARIANT.")
    finally:
        cur.close()
        conn.close()

def transformed_data():
    hook = SnowflakeHook(snowflake_conn_id="snowflake_default")
    
    # Liste des requêtes de transformation
    sql_queries = [
        """
        CREATE OR REPLACE TABLE ANALYTICS.DIM_CUSTOMERS AS
        SELECT v:id::INT as customer_id, v:first_name::STRING as first_name, 
               v:last_name::STRING as last_name, v:email::STRING as email
        FROM RAW.CUSTOMERS WHERE v IS NOT NULL;
        """,
        """
        CREATE OR REPLACE TABLE ANALYTICS.DIM_ACCOUNTS AS
        SELECT v:account_id::INT as account_id, v:customer_id::INT as customer_id, 
               v:account_type::STRING as account_type, v:balance::DECIMAL(15,2) as balance
        FROM RAW.ACCOUNTS WHERE v IS NOT NULL;
        """,
        """
        CREATE OR REPLACE TABLE ANALYTICS.FACT_TRANSACTIONS AS
        SELECT v:transaction_id::INT as transaction_id, v:account_id::INT as account_id, 
               v:amount::DECIMAL(15,2) as amount, v:transaction_date::TIMESTAMP as transaction_date
        FROM RAW.TRANSACTIONS WHERE v IS NOT NULL;
        """
    ]
    
    conn = hook.get_conn()
    cur = conn.cursor()
    try:
        for query in sql_queries:
            cur.execute(query)
        print("Transformation Silver terminée avec succès.")
    finally:
        cur.close()
        conn.close()

# -------- Airflow DAG --------
default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=1)
}

with DAG(
    dag_id="minio_to_snowflake_banking",
    default_args=default_args,
    description="Load MinIO parquet into Snowflake RAW tables",
    #schedule_interval="*/1 * * * *",
    schedule_interval=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
) as dag:

    task1 = PythonOperator(
        task_id="download_minio",
        python_callable=download_from_minio,
    )

    task2 = PythonOperator(
        task_id="load_snowflake",
        python_callable=load_to_snowflake,
        provide_context=True,
    )

    task3 = PythonOperator(
        task_id="transformed_data",
        python_callable=transformed_data,
        provide_context=True,
    )

    task1 >> task2 >> task3
