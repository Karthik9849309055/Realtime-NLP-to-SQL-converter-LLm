few_shot = [

    # ---------------- BASIC / INVENTORY ----------------
    {
        "Question": "How many t-shirts do we have left for Nike in XS size and white color?",
        "SQLQuery": "SELECT SUM(stock_quantity) FROM t_shirts WHERE brand = 'Nike' AND color = 'White' AND size = 'XS';",
        "Answer": "91"
    },
    {
        "Question": "How much is the total price of the inventory for all S-size t-shirts?",
        "SQLQuery": "SELECT SUM(price * stock_quantity) FROM t_shirts WHERE size = 'S';",
        "Answer": "22292"
    },
    {
        "Question": "How many white color Levi's t-shirts do we have?",
        "SQLQuery": "SELECT SUM(stock_quantity) FROM t_shirts WHERE brand = 'Levi' AND color = 'White';",
        "Answer": "290"
    },

    # ---------------- DISCOUNT / REVENUE ----------------
    {
        "Question": "If we have to sell all the Levi’s T-shirts today with discounts applied, how much revenue will be generated?",
        "SQLQuery": """
        SELECT SUM(a.total_amount * ((100 - COALESCE(d.pct_discount,0)) / 100))
        FROM (
            SELECT t_shirt_id, SUM(price * stock_quantity) AS total_amount
            FROM t_shirts
            WHERE brand = 'Levi'
            GROUP BY t_shirt_id
        ) a
        LEFT JOIN discounts d ON a.t_shirt_id = d.t_shirt_id;
        """,
        "Answer": "16725.4"
    },
    {
        "Question": "If we sell all Levi t-shirts today without any discount, how much revenue will be generated?",
        "SQLQuery": "SELECT SUM(price * stock_quantity) FROM t_shirts WHERE brand = 'Levi';",
        "Answer": "17462"
    },
    {
        "Question": "How much revenue will be generated if we sell all Nike L-size t-shirts after applying discounts?",
        "SQLQuery": """
        SELECT SUM(a.total_amount * ((100 - COALESCE(d.pct_discount,0)) / 100))
        FROM (
            SELECT t_shirt_id, SUM(price * stock_quantity) AS total_amount
            FROM t_shirts
            WHERE brand = 'Nike' AND size = 'L'
            GROUP BY t_shirt_id
        ) a
        LEFT JOIN discounts d ON a.t_shirt_id = d.t_shirt_id;
        """,
        "Answer": "Revenue after discount"
    },

    # ---------------- TRICKY AGGREGATIONS ----------------
    {
        "Question": "How many total t-shirts are available for each brand?",
        "SQLQuery": """
        SELECT brand, SUM(stock_quantity)
        FROM t_shirts
        GROUP BY brand;
        """,
        "Answer": "Grouped stock quantity by brand"
    },
    {
        "Question": "Which color has the highest total stock across all brands?",
        "SQLQuery": """
        SELECT color, SUM(stock_quantity) AS total_stock
        FROM t_shirts
        GROUP BY color
        ORDER BY total_stock DESC
        LIMIT 1;
        """,
        "Answer": "Color with maximum stock"
    },
    {
        "Question": "What is the average price of Nike t-shirts for each size?",
        "SQLQuery": """
        SELECT size, AVG(price)
        FROM t_shirts
        WHERE brand = 'Nike'
        GROUP BY size;
        """,
        "Answer": "Average price per size"
    },

    # ---------------- JOIN / EDGE CASES ----------------
    {
        "Question": "Which t-shirts have discounts applied?",
        "SQLQuery": """
        SELECT t.brand, t.color, t.size, d.pct_discount
        FROM t_shirts t
        JOIN discounts d ON t.t_shirt_id = d.t_shirt_id;
        """,
        "Answer": "List of discounted t-shirts"
    },
    {
        "Question": "Which t-shirts do not have any discount?",
        "SQLQuery": """
        SELECT t.brand, t.color, t.size
        FROM t_shirts t
        LEFT JOIN discounts d ON t.t_shirt_id = d.t_shirt_id
        WHERE d.t_shirt_id IS NULL;
        """,
        "Answer": "Non-discounted t-shirts"
    },
    {
        "Question": "Which brand has the highest total inventory value (price × stock)?",
        "SQLQuery": """
        SELECT brand, SUM(price * stock_quantity) AS total_value
        FROM t_shirts
        GROUP BY brand
        ORDER BY total_value DESC
        LIMIT 1;
        """,
        "Answer": "Brand with highest inventory value"
    }
]
