SELECT DATA_DATE, AVG(VALUE) OVER (ORDER BY DATA_DATE ASC ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS MOVING_AVERAGE_30 FROM STOCK_DATA;
SELECT DATA_DATE, VALUE, LAG(VALUE, 365) OVER (ORDER BY DATA_DATE) AS LAST_YEAR_VALUE, (VALUE - LAG(VALUE, 365) OVER (ORDER BY DATA_DATE)) * 100.0 / LAG(VALUE, 365) OVER (ORDER BY DATA_DATE) AS YOY_GROWTH FROM STOCK_DATA;
SELECT DATA_DATE, STDDEV(VALUE) OVER (ORDER BY DATA_DATE ASC ROWS BETWEEN 89 PRECEDING AND CURRENT ROW) AS ROLLING_VOLATILITY_90 FROM STOCK_DATA;
SELECT DATA_DATE, VALUE, AVG(VALUE) OVER (ORDER BY DATA_DATE ASC ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS MOVING_AVERAGE_5 FROM STOCK_DATA;
SELECT YEAR(DATA_DATE) AS YEAR, QUARTER(DATA_DATE) AS QUARTER, AVG(VALUE) AS AVERAGE_VALUE FROM STOCK_DATA GROUP BY YEAR, QUARTER ORDER BY YEAR, QUARTER;