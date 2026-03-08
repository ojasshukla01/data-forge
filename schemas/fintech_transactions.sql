-- Fintech: customers, accounts, cards, transactions, merchants, settlements
CREATE TABLE customers (
    id BIGINT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    created_at TIMESTAMP
);

CREATE TABLE accounts (
    id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    account_type VARCHAR(50) NOT NULL,
    balance_cents BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL,
    opened_at TIMESTAMP,
    closed_at TIMESTAMP,
    created_at TIMESTAMP
);

CREATE TABLE cards (
    id BIGINT PRIMARY KEY,
    account_id BIGINT NOT NULL REFERENCES accounts(id),
    card_type VARCHAR(20),
    last_four VARCHAR(4),
    expiry_date DATE,
    status VARCHAR(20),
    created_at TIMESTAMP
);

CREATE TABLE merchants (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    mcc_code VARCHAR(10),
    created_at TIMESTAMP
);

CREATE TABLE transactions (
    id BIGINT PRIMARY KEY,
    account_id BIGINT NOT NULL REFERENCES accounts(id),
    card_id BIGINT REFERENCES cards(id),
    merchant_id BIGINT REFERENCES merchants(id),
    amount_cents BIGINT NOT NULL,
    currency VARCHAR(3),
    status VARCHAR(20),
    transaction_date TIMESTAMP,
    settlement_date DATE,
    reversal_of_id BIGINT REFERENCES transactions(id),
    created_at TIMESTAMP
);

CREATE TABLE settlements (
    id BIGINT PRIMARY KEY,
    merchant_id BIGINT NOT NULL REFERENCES merchants(id),
    amount_cents BIGINT NOT NULL,
    status VARCHAR(20),
    settled_at TIMESTAMP,
    created_at TIMESTAMP
);

CREATE TABLE fraud_flags (
    id BIGINT PRIMARY KEY,
    transaction_id BIGINT NOT NULL REFERENCES transactions(id),
    flag_type VARCHAR(50),
    confidence_score FLOAT,
    flagged_at TIMESTAMP,
    created_at TIMESTAMP
);
