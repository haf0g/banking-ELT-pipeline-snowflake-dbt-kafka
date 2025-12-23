{{ config(materialized='table') }}

WITH latest AS (
    -- On garde TOUTES tes colonnes du snapshot pour l'historisation
    SELECT
        customer_id,
        first_name,
        last_name,
        email,
        created_at,
        dbt_valid_from   AS effective_from,
        dbt_valid_to     AS effective_to,
        CASE WHEN dbt_valid_to IS NULL THEN TRUE ELSE FALSE END AS is_current
    FROM {{ ref('customers_snapshot') }}
)

SELECT 
    *,
    -- On ajoute la nouvelle fonctionnalité de fidélité ici
    CASE 
        WHEN DATEDIFF('month', created_at, CURRENT_DATE()) >= 12 THEN 'Platine'
        WHEN DATEDIFF('month', created_at, CURRENT_DATE()) >= 6  THEN 'Or'
        ELSE 'Argent'
    END AS loyalty_class
FROM latest