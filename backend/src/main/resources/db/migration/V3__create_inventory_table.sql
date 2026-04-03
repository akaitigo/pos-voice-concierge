-- inventory テーブル: 在庫管理
CREATE TABLE inventory (
    product_id  VARCHAR(36)    PRIMARY KEY REFERENCES products(id),
    quantity    INTEGER        NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    updated_at  TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);
