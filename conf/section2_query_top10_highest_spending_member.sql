WITH data AS (
    SELECT
        membership_id,
        SUM(i.price * oi.quantity) as spending
    FROM orders o
    INNER JOIN orders_item oi
        ON o.order_id = oi.order_id
    INNER JOIN item i
        ON oi.item_id = i.item_id
    WHERE o.status = 'paid'
    GROUP BY 1
),
ranking AS (
    SELECT
        membership_id,
        spending,
        ROW_NUMBER() OVER (ORDER BY spending DESC) AS ranking
    FROM data
)
SELECT
    *
FROM ranking
WHERE ranking <= 10;