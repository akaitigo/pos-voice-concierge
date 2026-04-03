-- sales テーブル: 売上記録
CREATE TABLE sales (
    id          BIGSERIAL      PRIMARY KEY,
    product_id  VARCHAR(36)    NOT NULL REFERENCES products(id),
    quantity    INTEGER        NOT NULL CHECK (quantity > 0),
    unit_price  INTEGER        NOT NULL CHECK (unit_price >= 0),
    total_price INTEGER        NOT NULL CHECK (total_price >= 0),
    sold_at     TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sales_product_id ON sales (product_id);
CREATE INDEX idx_sales_sold_at ON sales (sold_at);
CREATE INDEX idx_sales_sold_at_product ON sales (sold_at, product_id);
