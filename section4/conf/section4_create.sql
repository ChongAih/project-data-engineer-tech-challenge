-- Dimension tables
CREATE TABLE IF NOT EXISTS covid (
    country varchar(255),
    measurement_date date,
    num_cases serial,
    num_p7d_avg_cases serial
);

CREATE UNIQUE INDEX IF NOT EXISTS covid_upsert_index ON covid (country, measurement_date);