USE sqlbasics;
-- inspect table structure
describe online_saledata;
-- row count
SELECT count(*) as total_recs
FROM online_saledata;

-- check sample
SELECT *
FROM online_saledata LIMIT 10;

-- duplicate check ROW_NUMBER() based on transaction fields for unique sale
with dup_temp as
(select *,
row_number() over (partition by 
InvoiceNo,
StockCode,
Quantity,
InvoiceDate,
CustomerID,
Country
 order by UnitPrice desc) row_num
from online_saledata)

select * from dup_temp
where row_num>1;

-- total sale of per country
select Country, round(sum(Quantity*UnitPrice),2) as total_sale
from online_saledata
group by Country
order by total_sale desc;

-- unique customer per country
select Country,
       count(distinct CustomerID) AS unq_customers
from online_saledata
group by Country
order by unq_customers desc;

-- Top 10 best selling product including ties
with tot_sold as
(select StockCode, sum(Quantity) as Qsold
from online_saledata
group by StockCode),
best_sold as
(select *, dense_rank() over (order by Qsold desc) as rnk
from tot_sold)
select * from best_sold
where rnk <=10
order by rnk asc;

-- daily sale percentage change 
WITH daily_sale AS (
    SELECT
        DATE(InvoiceDate) AS sale_date,
        ROUND(SUM(Quantity*UnitPrice), 2) AS tot_daily_sale
    FROM online_saledata
    GROUP BY DATE(InvoiceDate)
),
daily_comparison AS (
    SELECT
        sale_date,
        tot_daily_sale,
        LAG(tot_daily_sale) OVER (
            ORDER BY sale_date
        ) AS prev_daily_sale
    FROM daily_sale
)
SELECT
    sale_date,
    tot_daily_sale,
    prev_daily_sale,
    ROUND(
        (tot_daily_sale - prev_daily_sale)
        / NULLIF(prev_daily_sale, 0) * 100,
        2
    ) AS percent_change
FROM daily_comparison
ORDER BY sale_date;