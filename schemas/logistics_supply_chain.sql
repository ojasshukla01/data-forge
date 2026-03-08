-- Logistics & Supply Chain: warehouses, suppliers, products, POs, shipments, inventory, deliveries
CREATE TABLE warehouses (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    created_at TIMESTAMP
);

CREATE TABLE suppliers (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255),
    created_at TIMESTAMP
);

CREATE TABLE products (
    id BIGINT PRIMARY KEY,
    sku VARCHAR(100) UNIQUE,
    name VARCHAR(255) NOT NULL,
    unit_price_cents INTEGER NOT NULL,
    created_at TIMESTAMP
);

CREATE TABLE purchase_orders (
    id BIGINT PRIMARY KEY,
    supplier_id BIGINT NOT NULL REFERENCES suppliers(id),
    warehouse_id BIGINT NOT NULL REFERENCES warehouses(id),
    status VARCHAR(30) NOT NULL,
    order_date DATE,
    expected_date DATE,
    created_at TIMESTAMP
);

CREATE TABLE purchase_order_lines (
    id BIGINT PRIMARY KEY,
    purchase_order_id BIGINT NOT NULL REFERENCES purchase_orders(id),
    product_id BIGINT NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price_cents INTEGER NOT NULL,
    total_cents INTEGER NOT NULL,
    created_at TIMESTAMP
);

CREATE TABLE shipments (
    id BIGINT PRIMARY KEY,
    purchase_order_id BIGINT REFERENCES purchase_orders(id),
    warehouse_id BIGINT NOT NULL REFERENCES warehouses(id),
    status VARCHAR(30),
    shipped_at TIMESTAMP,
    created_at TIMESTAMP
);

CREATE TABLE inventory_movements (
    id BIGINT PRIMARY KEY,
    warehouse_id BIGINT NOT NULL REFERENCES warehouses(id),
    product_id BIGINT NOT NULL REFERENCES products(id),
    quantity_delta INTEGER NOT NULL,
    movement_type VARCHAR(30),
    reference_id BIGINT,
    created_at TIMESTAMP
);

CREATE TABLE deliveries (
    id BIGINT PRIMARY KEY,
    shipment_id BIGINT NOT NULL REFERENCES shipments(id),
    delivery_date DATE NOT NULL,
    status VARCHAR(30),
    created_at TIMESTAMP
);

CREATE TABLE returns (
    id BIGINT PRIMARY KEY,
    delivery_id BIGINT REFERENCES deliveries(id),
    shipment_id BIGINT REFERENCES shipments(id),
    reason VARCHAR(255),
    returned_at TIMESTAMP,
    created_at TIMESTAMP
);
