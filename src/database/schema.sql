-- Ledgera Database Schema

CREATE TABLE IF NOT EXISTS uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL,
    file_size_bytes INTEGER,
    mime_type TEXT,
    storage_path TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS detected_books (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_id UUID REFERENCES uploads(id) ON DELETE CASCADE,
    title TEXT,
    author TEXT,
    isbn TEXT,
    category TEXT,
    ocr_raw_text TEXT,
    ocr_confidence FLOAT,
    verified BOOLEAN DEFAULT FALSE,
    verification_source TEXT,
    cover_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID REFERENCES detected_books(id) ON DELETE CASCADE,
    source_name TEXT NOT NULL,
    source_url TEXT,
    content_snippet TEXT,
    reliability_score FLOAT,
    retrieved_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID REFERENCES detected_books(id) ON DELETE CASCADE,
    summary TEXT NOT NULL,
    best_for TEXT,
    not_ideal_for TEXT,
    public_sentiment TEXT,
    recommendation TEXT CHECK (recommendation IN ('buy', 'borrow', 'skip')),
    recommendation_reason TEXT,
    generated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS confidence_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID REFERENCES detected_books(id) ON DELETE CASCADE,
    overall_score FLOAT NOT NULL,
    ocr_confidence FLOAT,
    verification_confidence FLOAT,
    source_confidence FLOAT,
    review_confidence FLOAT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID REFERENCES detected_books(id) ON DELETE CASCADE,
    rating TEXT CHECK (rating IN ('helpful', 'not_helpful')),
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS eval_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_name TEXT,
    total_cases INTEGER,
    passed INTEGER,
    failed INTEGER,
    metrics JSONB,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_detected_books_upload ON detected_books(upload_id);
CREATE INDEX idx_sources_book ON sources(book_id);
CREATE INDEX idx_reviews_book ON reviews(book_id);
CREATE INDEX idx_feedback_book ON feedback(book_id);
