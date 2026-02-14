-- ============================================================
-- Database Initialization Script
-- Creates the database, roles, and grants permissions.
-- Run as a PostgreSQL superuser (e.g. postgres).
-- ============================================================

-- 1. Create application role
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'claims_app') THEN
        CREATE ROLE claims_app WITH LOGIN PASSWORD 'change_me_in_production';
    END IF;
END
$$;

-- 2. Create read-only role for reporting / BI tools
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'claims_readonly') THEN
        CREATE ROLE claims_readonly WITH LOGIN PASSWORD 'change_me_in_production';
    END IF;
END
$$;

-- 3. Database is created automatically by Docker (POSTGRES_DB env var)
-- No need for \connect — already connected to claims_db

-- 5. Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 6. Create application schema
CREATE SCHEMA IF NOT EXISTS claims AUTHORIZATION claims_app;

-- 7. Set default search path
ALTER DATABASE claims_db SET search_path TO claims, public;

-- 8. Grant privileges to application role
GRANT ALL PRIVILEGES ON DATABASE claims_db TO claims_app;
GRANT ALL PRIVILEGES ON SCHEMA claims TO claims_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA claims TO claims_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA claims TO claims_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA claims
    GRANT ALL PRIVILEGES ON TABLES TO claims_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA claims
    GRANT ALL PRIVILEGES ON SEQUENCES TO claims_app;

-- 9. Grant read-only privileges
GRANT CONNECT ON DATABASE claims_db TO claims_readonly;
GRANT USAGE ON SCHEMA claims TO claims_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA claims TO claims_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA claims
    GRANT SELECT ON TABLES TO claims_readonly;

-- 10. Schema is loaded separately via 02_schema.sql (Docker entrypoint)

-- Done
SELECT 'Database initialization complete' AS status;
