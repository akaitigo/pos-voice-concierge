-- products テーブル: 商品マスタ
CREATE TABLE products (
    id       VARCHAR(36)    PRIMARY KEY,
    name     VARCHAR(255)   NOT NULL UNIQUE,
    barcode  VARCHAR(13)    NOT NULL,
    price    INTEGER        NOT NULL CHECK (price >= 0)
);

CREATE INDEX idx_products_name ON products (name);
CREATE INDEX idx_products_barcode ON products (barcode);

-- aliases テーブル: 表記ゆれ辞書
CREATE TABLE aliases (
    alias        VARCHAR(255)   PRIMARY KEY,
    product_name VARCHAR(255)   NOT NULL REFERENCES products(name),
    created_at   TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_aliases_product_name ON aliases (product_name);
