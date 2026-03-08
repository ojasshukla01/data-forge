-- Social Platform: users, profiles, posts, comments, likes, follows, messages
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP
);

CREATE TABLE profiles (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE REFERENCES users(id),
    display_name VARCHAR(255),
    bio TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE posts (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    content TEXT,
    status VARCHAR(20),
    created_at TIMESTAMP
);

CREATE TABLE comments (
    id BIGINT PRIMARY KEY,
    post_id BIGINT NOT NULL REFERENCES posts(id),
    user_id BIGINT NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    created_at TIMESTAMP
);

CREATE TABLE likes (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    post_id BIGINT REFERENCES posts(id),
    comment_id BIGINT REFERENCES comments(id),
    created_at TIMESTAMP
);

CREATE TABLE follows (
    id BIGINT PRIMARY KEY,
    follower_id BIGINT NOT NULL REFERENCES users(id),
    followed_id BIGINT NOT NULL REFERENCES users(id),
    created_at TIMESTAMP
);

CREATE TABLE messages (
    id BIGINT PRIMARY KEY,
    sender_id BIGINT NOT NULL REFERENCES users(id),
    receiver_id BIGINT NOT NULL REFERENCES users(id),
    content TEXT,
    read_at TIMESTAMP,
    created_at TIMESTAMP
);

CREATE TABLE reports (
    id BIGINT PRIMARY KEY,
    reporter_id BIGINT NOT NULL REFERENCES users(id),
    post_id BIGINT REFERENCES posts(id),
    comment_id BIGINT REFERENCES comments(id),
    reason VARCHAR(100),
    status VARCHAR(20),
    created_at TIMESTAMP
);
