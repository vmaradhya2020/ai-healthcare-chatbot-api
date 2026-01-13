-- =============================================================================
-- MySQL Database Setup for Healthcare Chatbot API
-- =============================================================================
-- This script creates the database and user for the application
-- Run this as MySQL root user

-- Create database
CREATE DATABASE IF NOT EXISTS healthcaresense
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Create application user (change password in production!)
CREATE USER IF NOT EXISTS 'healthcareapp'@'localhost' IDENTIFIED BY 'Sairam@12345';

-- Grant privileges
GRANT ALL PRIVILEGES ON healthcaresense.* TO 'healthcareapp'@'localhost';

-- If you need remote access (development only, not for production!)
-- CREATE USER IF NOT EXISTS 'healthcareapp'@'%' IDENTIFIED BY 'Change_This_Password_123!';
-- GRANT ALL PRIVILEGES ON healthcaresense.* TO 'healthcareapp'@'%';

-- Apply changes
FLUSH PRIVILEGES;

-- Verify database creation
SHOW DATABASES LIKE 'healthcaresense';

-- Verify user creation
SELECT User, Host FROM mysql.user WHERE User = 'healthcareapp';

-- Show grants for user
SHOW GRANTS FOR 'healthcareapp'@'localhost';

-- =============================================================================
-- Connection String Format:
-- =============================================================================
-- DATABASE_URL=mysql+pymysql://healthcareapp:Change_This_Password_123!@localhost:3306/healthcaresense
--
-- Make sure to:
-- 1. Change the password above
-- 2. Update your .env file with the connection string
-- 3. Never commit the .env file to version control
-- =============================================================================
