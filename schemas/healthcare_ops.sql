-- Healthcare: patients, providers, appointments, encounters, diagnoses, prescriptions, claims
CREATE TABLE patients (
    id BIGINT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    created_at TIMESTAMP
);

CREATE TABLE providers (
    id BIGINT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    specialty VARCHAR(100),
    npi VARCHAR(20),
    created_at TIMESTAMP
);

CREATE TABLE appointments (
    id BIGINT PRIMARY KEY,
    patient_id BIGINT NOT NULL REFERENCES patients(id),
    provider_id BIGINT NOT NULL REFERENCES providers(id),
    appointment_date DATE NOT NULL,
    status VARCHAR(30),
    created_at TIMESTAMP
);

CREATE TABLE encounters (
    id BIGINT PRIMARY KEY,
    patient_id BIGINT NOT NULL REFERENCES patients(id),
    provider_id BIGINT NOT NULL REFERENCES providers(id),
    appointment_id BIGINT REFERENCES appointments(id),
    encounter_date DATE NOT NULL,
    encounter_type VARCHAR(50),
    created_at TIMESTAMP
);

CREATE TABLE diagnoses (
    id BIGINT PRIMARY KEY,
    encounter_id BIGINT NOT NULL REFERENCES encounters(id),
    patient_id BIGINT NOT NULL REFERENCES patients(id),
    icd_code VARCHAR(20),
    description VARCHAR(255),
    created_at TIMESTAMP
);

CREATE TABLE prescriptions (
    id BIGINT PRIMARY KEY,
    encounter_id BIGINT NOT NULL REFERENCES encounters(id),
    patient_id BIGINT NOT NULL REFERENCES patients(id),
    provider_id BIGINT NOT NULL REFERENCES providers(id),
    medication_name VARCHAR(255),
    dosage VARCHAR(100),
    prescription_date DATE NOT NULL,
    created_at TIMESTAMP
);

CREATE TABLE claims (
    id BIGINT PRIMARY KEY,
    patient_id BIGINT NOT NULL REFERENCES patients(id),
    provider_id BIGINT NOT NULL REFERENCES providers(id),
    encounter_id BIGINT REFERENCES encounters(id),
    amount_cents BIGINT NOT NULL,
    status VARCHAR(30),
    submitted_at TIMESTAMP,
    paid_at TIMESTAMP,
    created_at TIMESTAMP
);
