# Dockerfile-airflow
FROM apache/airflow:2.9.3

USER root
# Install git (needed for dbt packages)
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean


# Switch to airflow user first
USER airflow

# Install dbt packages
RUN pip install --no-cache-dir dbt-core dbt-snowflake
