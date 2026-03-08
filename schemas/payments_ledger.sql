-- Payments Ledger: customers, invoices, payments, methods, ledger entries, refunds
CREATE TABLE customers (
    id BIGINT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    created_at TIMESTAMP
);

CREATE TABLE payment_methods (
    id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    method_type VARCHAR(50),
    last_four VARCHAR(4),
    created_at TIMESTAMP
);

CREATE TABLE invoices (
    id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    total_cents BIGINT NOT NULL,
    status VARCHAR(30),
    due_date DATE,
    paid_at TIMESTAMP,
    created_at TIMESTAMP
);

CREATE TABLE payments (
    id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    invoice_id BIGINT REFERENCES invoices(id),
    payment_method_id BIGINT REFERENCES payment_methods(id),
    amount_cents BIGINT NOT NULL,
    status VARCHAR(30),
    payment_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP
);

CREATE TABLE ledger_entries (
    id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    amount_cents BIGINT NOT NULL,
    entry_type VARCHAR(30),
    reference_id BIGINT,
    entry_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP
);

CREATE TABLE refunds (
    id BIGINT PRIMARY KEY,
    payment_id BIGINT NOT NULL REFERENCES payments(id),
    amount_cents BIGINT NOT NULL,
    reason VARCHAR(255),
    refund_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP
);

CREATE TABLE disputes (
    id BIGINT PRIMARY KEY,
    payment_id BIGINT NOT NULL REFERENCES payments(id),
    reason VARCHAR(255),
    status VARCHAR(30),
    dispute_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP
);
