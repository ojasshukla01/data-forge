-- AdTech: advertisers, campaigns, ad groups, creatives, impressions, clicks, conversions
CREATE TABLE advertisers (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    created_at TIMESTAMP
);

CREATE TABLE campaigns (
    id BIGINT PRIMARY KEY,
    advertiser_id BIGINT NOT NULL REFERENCES advertisers(id),
    name VARCHAR(255) NOT NULL,
    status VARCHAR(20),
    start_date DATE,
    end_date DATE,
    budget_cents BIGINT,
    created_at TIMESTAMP
);

CREATE TABLE ad_groups (
    id BIGINT PRIMARY KEY,
    campaign_id BIGINT NOT NULL REFERENCES campaigns(id),
    name VARCHAR(255) NOT NULL,
    status VARCHAR(20),
    created_at TIMESTAMP
);

CREATE TABLE creatives (
    id BIGINT PRIMARY KEY,
    ad_group_id BIGINT NOT NULL REFERENCES ad_groups(id),
    creative_type VARCHAR(50),
    status VARCHAR(20),
    created_at TIMESTAMP
);

CREATE TABLE impressions (
    id BIGINT PRIMARY KEY,
    creative_id BIGINT NOT NULL REFERENCES creatives(id),
    ad_group_id BIGINT NOT NULL REFERENCES ad_groups(id),
    campaign_id BIGINT NOT NULL REFERENCES campaigns(id),
    impression_date DATE,
    created_at TIMESTAMP
);

CREATE TABLE clicks (
    id BIGINT PRIMARY KEY,
    impression_id BIGINT REFERENCES impressions(id),
    creative_id BIGINT NOT NULL REFERENCES creatives(id),
    click_date DATE,
    created_at TIMESTAMP
);

CREATE TABLE conversions (
    id BIGINT PRIMARY KEY,
    click_id BIGINT REFERENCES clicks(id),
    creative_id BIGINT REFERENCES creatives(id),
    conversion_date DATE,
    value_cents BIGINT,
    created_at TIMESTAMP
);

CREATE TABLE spend_reports (
    id BIGINT PRIMARY KEY,
    campaign_id BIGINT NOT NULL REFERENCES campaigns(id),
    report_date DATE NOT NULL,
    spend_cents BIGINT NOT NULL,
    impressions_count BIGINT,
    clicks_count BIGINT,
    created_at TIMESTAMP
);
