-- IoT Telemetry: devices, models, locations, readings, alerts, maintenance
CREATE TABLE device_models (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    manufacturer VARCHAR(255),
    created_at TIMESTAMP
);

CREATE TABLE locations (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    latitude FLOAT,
    longitude FLOAT,
    created_at TIMESTAMP
);

CREATE TABLE devices (
    id BIGINT PRIMARY KEY,
    device_model_id BIGINT NOT NULL REFERENCES device_models(id),
    location_id BIGINT REFERENCES locations(id),
    serial_number VARCHAR(100) UNIQUE,
    status VARCHAR(20),
    installed_at TIMESTAMP,
    created_at TIMESTAMP
);

CREATE TABLE telemetry_readings (
    id BIGINT PRIMARY KEY,
    device_id BIGINT NOT NULL REFERENCES devices(id),
    reading_type VARCHAR(50),
    value FLOAT,
    unit VARCHAR(20),
    recorded_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP
);

CREATE TABLE alerts (
    id BIGINT PRIMARY KEY,
    device_id BIGINT NOT NULL REFERENCES devices(id),
    telemetry_reading_id BIGINT REFERENCES telemetry_readings(id),
    alert_type VARCHAR(50),
    severity VARCHAR(20),
    triggered_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP
);

CREATE TABLE maintenance_events (
    id BIGINT PRIMARY KEY,
    device_id BIGINT NOT NULL REFERENCES devices(id),
    event_type VARCHAR(50),
    maintenance_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP
);
