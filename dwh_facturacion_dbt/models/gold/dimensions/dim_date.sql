{{ config(materialized='table') }}

WITH date_spine AS (

    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2015-01-01' as date)",
        end_date="cast('2030-12-31' as date)"
    ) }}

)

SELECT
    date_day::date AS date,
    EXTRACT(YEAR FROM date_day) AS year,
    EXTRACT(MONTH FROM date_day) AS month,
    EXTRACT(DAY FROM date_day) AS day,
    EXTRACT(QUARTER FROM date_day) AS quarter,
    TO_CHAR(date_day, 'Month') AS month_name,
    TO_CHAR(date_day, 'Day') AS day_name,
    CASE WHEN EXTRACT(ISODOW FROM date_day) IN (6,7) THEN TRUE ELSE FALSE END AS is_weekend
FROM date_spine