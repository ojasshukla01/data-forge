-- HR Workforce: employees, departments, roles, payroll, leave, performance
CREATE TABLE departments (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP
);

CREATE TABLE roles (
    id BIGINT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    level VARCHAR(20),
    created_at TIMESTAMP
);

CREATE TABLE employees (
    id BIGINT PRIMARY KEY,
    department_id BIGINT NOT NULL REFERENCES departments(id),
    role_id BIGINT NOT NULL REFERENCES roles(id),
    manager_id BIGINT REFERENCES employees(id),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    hire_date DATE NOT NULL,
    created_at TIMESTAMP
);

CREATE TABLE payroll (
    id BIGINT PRIMARY KEY,
    employee_id BIGINT NOT NULL REFERENCES employees(id),
    pay_period_start DATE NOT NULL,
    pay_period_end DATE NOT NULL,
    gross_cents BIGINT NOT NULL,
    net_cents BIGINT NOT NULL,
    created_at TIMESTAMP
);

CREATE TABLE leave_requests (
    id BIGINT PRIMARY KEY,
    employee_id BIGINT NOT NULL REFERENCES employees(id),
    leave_start DATE NOT NULL,
    leave_end DATE NOT NULL,
    status VARCHAR(30),
    created_at TIMESTAMP
);

CREATE TABLE performance_reviews (
    id BIGINT PRIMARY KEY,
    employee_id BIGINT NOT NULL REFERENCES employees(id),
    review_date DATE NOT NULL,
    rating INTEGER,
    reviewer_id BIGINT REFERENCES employees(id),
    created_at TIMESTAMP
);
