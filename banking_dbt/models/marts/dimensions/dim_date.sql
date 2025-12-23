{{ config(materialized='table') }}

WITH date_spine AS (
    -- Génère une liste de dates de 2024 à 2026
    SELECT 
        DATEADD(day, seq4(), '2024-01-01') AS date_day
    FROM TABLE(GENERATOR(ROWCOUNT => 1095)) -- 3 ans environ
)

SELECT
    date_day AS date_id,
    YEAR(date_day) AS year,
    MONTH(date_day) AS month,
    MONTHNAME(date_day) AS month_name,
    QUARTER(date_day) AS quarter,
    DAYOFWEEK(date_day) AS day_of_week,
    DAYNAME(date_day) AS day_name,
    CASE WHEN DAYOFWEEK(date_day) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend
FROM date_spine