-- Standalone SQL file with three CREATE TABLE statements.
-- This fixture is aspirational: the SQL file extractor is out of scope for Phase 4.
-- When the extractor ships, this file should produce 3 schema primitives.

CREATE TABLE author (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE book (
    id INTEGER PRIMARY KEY,
    author_id INTEGER,
    title TEXT NOT NULL,
    FOREIGN KEY (author_id) REFERENCES author(id)
);

CREATE TABLE review (
    id INTEGER PRIMARY KEY,
    book_id INTEGER,
    rating INTEGER NOT NULL,
    FOREIGN KEY (book_id) REFERENCES book(id)
);
