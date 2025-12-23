# 🏦 Snowflake and dbt banking data pipeline (with Kafka, MinIO Airflow, Power BI)

![Snowflake](https://img.shields.io/badge/Snowflake-29B5E8?logo=snowflake&logoColor=white)
![DBT](https://img.shields.io/badge/dbt-FF694B?logo=dbt&logoColor=white)
![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-017CEE?logo=apacheairflow&logoColor=white)
![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-231F20?logo=apachekafka&logoColor=white)
![Debezium](https://img.shields.io/badge/Debezium-EF3B2D?logo=apache&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-F2C811?logo=powerbi&logoColor=black)

---

## 📌 Project Overview

This project demonstrates an **end-to-end modern data stack pipeline** for the **banking domain**, implementing **Medallion Architecture** with **real-time streaming CDC**. The objective is to capture transaction flows and customer profile changes in real-time, historize them using **SCD Type 2** mechanisms, and deliver reliable strategic dashboards.

The solution relies on a robust **ELT** (Extract, Load, Transform) architecture, orchestrated by **Airflow** and transformed by **dbt** within **Snowflake**, following **best practices of CI/CD and data warehousing**.

👉 Think of it as a **production-grade banking data ecosystem** built on modern data tools.

---

## 🏗️ Architecture

<img width="797" height="343" alt="image" src="https://github.com/user-attachments/assets/bc46f9a4-295c-4b57-acce-28f3b998cc7f" />

### Pipeline Flow

1. **Data Generation** → Simulates banking data (customers, accounts, transactions) using Python (Faker) into PostgreSQL
2. **Streaming & CDC** → Debezium captures changes (WAL) from Postgres and publishes them to Kafka
3. **Landing Zone** → A Python consumer stores Kafka messages as Parquet files in MinIO (S3-compatible storage)
4. **Orchestration** → Airflow manages the transfer from MinIO to Snowflake and triggers dbt transformations
5. **Data Warehouse** → Snowflake hosts data across Bronze, Silver, and Gold layers
6. **Transformation** → dbt cleans, deduplicates, and historizes data
7. **Visualization** → Power BI & Tableau consume final data marts

---

## ⚡ Tech Stack

- **Snowflake** → Cloud Data Warehouse (Bronze → Silver → Gold)
- **dbt** → Transformations, testing, snapshots (SCD Type-2)
- **Apache Airflow** → Orchestration & DAG scheduling
- **Apache Kafka + Debezium** → Real-time streaming & Change Data Capture
- **MinIO** → S3-compatible object storage
- **PostgreSQL** → Source OLTP system with ACID guarantees
- **Python (Faker)** → Data simulation & Kafka consumer
- **Docker & docker-compose** → Containerized infrastructure
- **Power BI** → Business Intelligence & dashboards
- **Git & GitHub Actions** → CI/CD workflows

---

## ✅ Key Features

- **Real-time Change Data Capture (CDC)** via Kafka + Debezium capturing PostgreSQL WAL
- **Medallion Architecture** (Bronze → Silver → Gold) for data quality progression
- **SCD Type 2 snapshots** for complete historical tracking of customers and accounts
- **Semi-structured data ingestion** using Snowflake VARIANT type for schema flexibility
- **14 automated data quality tests** ensuring banking data reliability
- **Star Schema modeling** optimized for BI performance
- **Automated pipeline orchestration** using Airflow DAGs
- **CI/CD pipeline** with dbt tests + GitHub Actions
- **Strategic dashboards** for banking KPIs and insights

---

## 📂 Repository Structure

```text
banking-modern-datastack/
├── .github/workflows/         # CI/CD pipelines (ci.yml, cd.yml)
├── banking_dbt/              # dbt project
│   ├── models/
│   │   ├── staging/           # JSON flattening & deduplication
│   │   ├── marts/             # Facts & dimensions (Star Schema)
│   │   └── sources.yml
│   ├── snapshots/             # SCD Type-2 for accounts & customers
│   ├── tests/                 # Data quality tests
│   └── dbt_project.yml
├── consumer/
│   └── kafka_to_minio.py     # Kafka consumer → Parquet → MinIO
├── data-generator/            # Faker-based banking data simulator
│   └── faker_generator.py
├── docker/
│   ├── dags/                  # Airflow DAGs
│   │   ├── minio_to_snowflake_banking.py
│   │   └── SCD2_snapshots.py
│   └── plugins/               # Custom operators
├── kafka-debezium/            # Kafka connectors & CDC configuration
│   └── generate_and_post_connector.py
├── postgres/                  # PostgreSQL schema (OLTP DDL & seeds)
│   └── schema.sql
├── powerbi/                   # Power BI dashboard files
│   └── banking_strategic_dashboard.pbix
├── .gitignore
├── docker-compose.yml         # Complete containerized infrastructure
├── dockerfile-airflow.dockerfile
├── requirements.txt
└── README.md
```

---

## ⚙️ Technical Implementation Phases

### **Phase 1: Semi-Structured Data Ingestion (Bronze Layer)**

Data arrives from Kafka in raw JSON format. To ensure pipeline resilience against schema evolution, we use Snowflake's **VARIANT** type.

- **Mechanism**: Loading via PUT and COPY INTO orchestrated by Airflow
- **RAW Schema**: Storing complete JSON objects to enable full reprocessing if needed
- **Technology**: Snowflake VARIANT, Apache Airflow, MinIO

**Challenge solved**: Schema flexibility for evolving data structures without breaking the pipeline.

---

### **Phase 2: Orchestration with Apache Airflow**

The entire pipeline is automated through two main DAGs:

- **minio_to_snowflake_banking**: Manages physical file transfer and initial ingestion
- **SCD2_snapshots**: Handles intelligent processing (dbt snapshot, run, test)

**Security**: Using SnowflakeHook for centralized connection management.

**DAG Features**:
- Error handling and retry logic
- Task dependencies and parallelization
- Monitoring and alerting capabilities

---

### **Phase 3: Analytics Engineering with dbt**

The transformation from raw to analytics-ready format follows three stages:

#### **Staging Models**
- JSON field extraction and data typing
- Deduplication using `ROW_NUMBER()` window functions
- Data cleaning and standardization

#### **Snapshots (SCD Type 2)**
- Complete traceability of account and customer modifications
- Tracking changes in email, name, balance, and account status
- Valid_from and valid_to timestamps for temporal queries

#### **Feature Engineering**
- Calculation of **Customer Loyalty Class** (Platinum, Gold, Silver) based on customer tenure (months_active)
- Aggregated transaction metrics per customer
- Account activity indicators

**Models Architecture**:
```
staging/
├── stg_customers
├── stg_accounts
└── stg_transactions

marts/
├── dim_customers (with loyalty segmentation)
├── dim_accounts
├── dim_date
└── fact_transactions
```

---

### **Phase 4: Data Quality & Integrity**

Implementation of **14 automated tests** to validate banking data reliability:

| Test Category | Tests Implemented |
|--------------|-------------------|
| **Uniqueness** | Primary keys on all dimensions and facts |
| **Not Null** | Critical fields (customer_id, account_id, transaction_id) |
| **Referential Integrity** | Relationships between Facts and Dimensions |
| **Accepted Values** | Transaction statuses (COMPLETED, FAILED, PENDING) |
| **Custom Tests** | Balance consistency, date logic validation |

**Testing Framework**: dbt native tests + custom schema tests

---

### **Phase 5: BI Modeling (Star Schema)**

The Power BI dashboard is built on a **pure star schema** to optimize performance and query simplicity:

> Semantic Model :

<img width="924" height="683" alt="Capture d&#39;écran 2025-12-23 085214" src="https://github.com/user-attachments/assets/435889bd-8264-4c8f-9f19-1b40794a28c0" />

#### **Fact Table**
- **FACT_TRANSACTIONS**: Contains transaction amounts, dates, IDs, and foreign keys
- Grain: One row per transaction
- Measures: Total amount, transaction count, success rate

#### **Dimension Tables**
- **DIM_CUSTOMERS**: Customer attributes with loyalty segmentation
- **DIM_ACCOUNTS**: Account details, types, and statuses
- **DIM_DATE**: Calendar dimension for time intelligence

**Challenges Resolved**:
- Fixed ambiguous filter path relationships by denormalizing customer_id into the fact table
- Synchronized temporal granularity (Date vs DateTime) between Snowflake and Power BI
- Created calculated column `Date_Link` to connect timestamps with calendar dimension

---

## 🚀 Getting Started

### **Prerequisites**

- Docker & Docker Compose installed
- Active Snowflake account
- Git for version control
- (Optional) Power BI Desktop for dashboard

### **Installation & Setup**

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd banking-project

# 2. Configure Snowflake credentials
# Create banking_dbt/.dbt/profiles.yml with your Snowflake credentials

# 3. Start the infrastructure (Airflow, Kafka, MinIO, Postgres)
docker-compose up -d --build

# 4. Initialize CDC with Debezium
python kafka-debezium/generate_and_post_connector.py

# 5. Verify services are running
docker-compose ps
```

### **Running the Pipeline**

1. **Access Airflow UI**: Navigate to [http://localhost:8080](http://localhost:8080)
   - Username: `admin`
   - Password: `admin`

2. **Activate DAGs**: Enable both DAGs in the Airflow UI

3. **Trigger Pipeline**:
   - First trigger: `minio_to_snowflake_banking`
   - Then trigger: `SCD2_snapshots`

4. **Monitor Execution**: Check task logs and status in Airflow

### **Accessing the Data**

```sql
-- Query Snowflake to verify data
USE DATABASE BANKING;
USE SCHEMA MARTS;

-- Check customer loyalty distribution
SELECT loyalty_class, COUNT(*) as customer_count
FROM dim_customers
GROUP BY loyalty_class;

-- Check transaction success rate
SELECT 
    transaction_status,
    COUNT(*) as transaction_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM fact_transactions
GROUP BY transaction_status;
```

---

## 📊 Business Intelligence & Insights

### **Strategic Banking Dashboard**

The final deliverable is a comprehensive **Power BI dashboard** titled **"Strategic Banking Piloting"** that answers critical business questions:

> The dashboard :
<img width="954" height="539" alt="Capture d&#39;écran 2025-12-23 081731" src="https://github.com/user-attachments/assets/f8559cbc-88ed-4ed2-88ad-b5980f564371" />



#### **Key Metrics Tracked**

1. **Asset Distribution by Loyalty Class**
   - Total deposits segmented by Platinum, Gold, and Silver customers
   - Identifies high-value customer segments

2. **Transaction Success Rate**
   - Success percentage by account type
   - Helps identify operational issues and account-specific problems

3. **Monthly Deposit Evolution**
   - Trend analysis of global deposits month-over-month
   - Seasonal patterns and growth indicators

4. **Customer Segmentation Analysis**
   - Distribution of customers across loyalty tiers
   - Customer lifetime value indicators

5. **Account Performance Metrics**
   - Active vs inactive accounts
   - Account type distribution and preferences

#### **Dashboard Features**

- **Interactive Filters**: Date range, customer segment, account type
- **Drill-Down Capabilities**: From summary to transaction-level detail
- **Time Intelligence**: Month-over-month, year-over-year comparisons
- **Visual Variety**: Cards, bar charts, line charts, pie charts for different insights
- **Real-Time Updates**: Refreshes as new data flows through the pipeline

#### **Business Value**

The dashboard enables stakeholders to:
- Make data-driven decisions on customer retention strategies
- Identify and address operational inefficiencies
- Monitor business health in real-time
- Optimize resource allocation based on customer segments
- Track KPIs against strategic goals

---

## 🔄 CI/CD Pipeline

### **Continuous Integration (ci.yml)**
- Linting and code quality checks
- dbt compile to validate models
- Run dbt tests on pull requests
- Prevents broken code from merging

### **Continuous Deployment (cd.yml)**
- Automated deployment on merge to main
- Deploy Airflow DAGs
- Run dbt models in production
- Update Snowflake schemas

---

## 📈 Future Enhancements

- [ ] Add real-time alerting for transaction anomalies
- [ ] Implement machine learning models for fraud detection
- [ ] Expand to additional data sources (credit cards, loans)
- [ ] Add data lineage visualization
- [ ] Implement data governance policies
- [ ] Create Tableau dashboards as alternative to Power BI
- [ ] Add customer churn prediction models

---

## 📚 Documentation

For more detailed documentation on specific components:
- [dbt Models Documentation](./banking_dbt/README.md)
- [Airflow DAGs Documentation](./docker/dags/README.md)
- [Kafka Setup Guide](./kafka-debezium/README.md)

---

## 👨‍💻 Author

**Developed by**: Hafid Garhoum & Khawla Darhami & Nora Boucetta & Hasnae Asbai
**Date**: December 2025
**Course**: Big Data & Applications

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Inspired by modern data engineering best practices
- Built following the Medallion Architecture pattern
- Thanks to the open-source community for amazing tools

---


**⭐ If you found this project helpful, please give it a star!**



