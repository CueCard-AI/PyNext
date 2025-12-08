-- PyNext Test Database Initialization
-- This script runs when the PostgreSQL container starts for the first time.

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create test schemas
CREATE SCHEMA IF NOT EXISTS pynext_test;
CREATE SCHEMA IF NOT EXISTS pynext_integration;

-- Grant permissions
GRANT ALL ON SCHEMA pynext_test TO pynext;
GRANT ALL ON SCHEMA pynext_integration TO pynext;

-- Set search path
ALTER DATABASE pynext_test SET search_path TO public, pynext_test;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'PyNext test database initialized successfully!';
END $$;

