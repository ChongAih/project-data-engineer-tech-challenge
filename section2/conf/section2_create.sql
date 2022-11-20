-- Dimension tables
CREATE TABLE IF NOT EXISTS manufacturer (
    manufacturer_id varchar(255) NOT NULL PRIMARY KEY,
    manufacturer_name varchar(255),
    create_time serial,
    update_time serial
);

CREATE TABLE IF NOT EXISTS member (
    membership_id varchar(255) NOT NULL PRIMARY KEY,
    first_name varchar(50),
    last_name varchar(50),
    date_of_birth varchar(10),
    mobile_no serial,
    email varchar(50),
    create_time serial,
    update_time serial
);

CREATE TABLE IF NOT EXISTS item (
    item_id varchar(255) NOT NULL PRIMARY KEY,
    item_name varchar(255),
    price real,
    weight real,
    stock_keeping_unit serial,
    create_time serial,
    update_time serial,
    manufacturer_id varchar(255),
    CONSTRAINT fk_manufacturer_id
        FOREIGN KEY (manufacturer_id)
        REFERENCES manufacturer(manufacturer_id)
);

-- Fact tables
CREATE TABLE IF NOT EXISTS orders (
    order_id varchar(255) NOT NULL PRIMARY KEY,
    status varchar(255), -- new, paid, complete, delivering, abandoned
    order_level_discount serial,
    shipping varchar(255),
    create_time serial,
    update_time serial,
    membership_id varchar(255),
    CONSTRAINT fk_membership_id
        FOREIGN KEY (membership_id)
        REFERENCES member(membership_id)
);

CREATE TABLE IF NOT EXISTS orders_item (
    order_item_id varchar(255) NOT NULL PRIMARY KEY,
    quantity serial,
    item_level_discount serial,
    create_time serial,
    update_time serial,
    order_id varchar(255),
    item_id varchar(255),
    CONSTRAINT fk_order_id
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id),
    CONSTRAINT fk_item_id
        FOREIGN KEY (item_id)
        REFERENCES item(item_id)
);

CREATE TABLE IF NOT EXISTS txn (
    txn_id varchar(255) NOT NULL PRIMARY KEY,
    payment_mode varchar(255), -- cash on delivery, credit, debit, cheque
    status varchar(255), -- cancelled, failed, rejected, success
    create_time serial,
    update_time serial,
    order_id varchar(255),
    membership_id varchar(255),
    CONSTRAINT fk_order_id
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
    CONSTRAINT fk_membership_id FOREIGN KEY (membership_id) REFERENCES member(membership_id)
);

-- Create index for fast query if needed
--CREATE INDEX IF NOT EXISTS manufacturer__manufacturer_id_index ON manufacturer (manufacturer_id);
--CREATE INDEX IF NOT EXISTS item__item_id_index ON item (item_id);
--CREATE INDEX IF NOT EXISTS member__membership_id_index ON member (membership_id);
--CREATE INDEX IF NOT EXISTS orders__order_id_index ON orders (order_id);
--CREATE INDEX IF NOT EXISTS orders_item__order_item_id_index ON orders_item (order_item_id);
--CREATE INDEX IF NOT EXISTS txn__txn_id_index ON txn (txn_id);