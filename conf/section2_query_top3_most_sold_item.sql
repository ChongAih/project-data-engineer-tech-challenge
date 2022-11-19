WITH data AS (
    SELECT
        item_id,
        SUM(quantity) AS sold_amount
    FROM orders_item oi
    INNER JOIN orders o
        ON o.order_id = oi.order_id
    WHERE o.status = 'paid'
    GROUP BY 1
),
ranking AS (
    SELECT
        item_id,
        sold_amount,
        ROW_NUMBER() OVER (ORDER BY sold_amount DESC) AS ranking
    FROM data
)
SELECT
    *
FROM ranking
WHERE ranking <= 3;