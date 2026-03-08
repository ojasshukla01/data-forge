-- SaaS / CRM billing & subscriptions schema (DDL for schema ingest)
CREATE TABLE organizations (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES organizations(id),
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    role VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE plans (
    id BIGINT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    amount_cents INTEGER NOT NULL,
    interval VARCHAR(20),
    created_at TIMESTAMP
);

CREATE TABLE subscriptions (
    id BIGINT PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES organizations(id),
    plan_id BIGINT NOT NULL REFERENCES plans(id),
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    created_at TIMESTAMP
);

CREATE TABLE invoices (
    id BIGINT PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES organizations(id),
    subscription_id BIGINT REFERENCES subscriptions(id),
    total_cents INTEGER NOT NULL,
    status VARCHAR(20),
    due_date DATE,
    paid_at TIMESTAMP,
    created_at TIMESTAMP
);

CREATE TABLE invoice_line_items (
    id BIGINT PRIMARY KEY,
    invoice_id BIGINT NOT NULL REFERENCES invoices(id),
    description VARCHAR(255),
    quantity INTEGER NOT NULL,
    unit_price_cents INTEGER NOT NULL,
    amount_cents INTEGER NOT NULL,
    created_at TIMESTAMP
);

CREATE TABLE support_tickets (
    id BIGINT PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES organizations(id),
    user_id BIGINT REFERENCES users(id),
    subject VARCHAR(255),
    status VARCHAR(50),
    priority VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
