-- SQL Buddy: Database Cleanup Script
-- Phase IV - CS 5200 Database Project
-- Group 11: SQL Buddy

USE sqlbuddy;

-- DROP TRIGGERS

DROP TRIGGER IF EXISTS before_attempt_insert;
DROP TRIGGER IF EXISTS before_attempt_update;
DROP TRIGGER IF EXISTS after_problem_insert;
DROP TRIGGER IF EXISTS after_high_score_attempt;
DROP TRIGGER IF EXISTS before_problem_delete;

-- DROP PROCEDURES

DROP PROCEDURE IF EXISTS RegisterAttempt;
DROP PROCEDURE IF EXISTS GetStudentProgressReport;

-- DROP FUNCTIONS

DROP FUNCTION IF EXISTS GetStudentLevel;
DROP FUNCTION IF EXISTS GetProblemAvgScore;

-- DROP VIEWS

DROP VIEW IF EXISTS StudentPerformanceSummary;
DROP VIEW IF EXISTS ProblemStatistics;
DROP VIEW IF EXISTS MentorActivityDashboard;

-- DROP TABLES (M:N Relationship Tables First)
-- Drop relationship tables first to avoid FK constraint issues

DROP TABLE IF EXISTS Receive;
DROP TABLE IF EXISTS Send;
DROP TABLE IF EXISTS Access;
DROP TABLE IF EXISTS ResourceTopic;
DROP TABLE IF EXISTS Have_topic;

-- DROP MAIN TABLES (in dependency order)
-- Drop tables with FKs to other tables first

DROP TABLE IF EXISTS Attempt;
DROP TABLE IF EXISTS Notification;
DROP TABLE IF EXISTS Resource;
DROP TABLE IF EXISTS Problem;
DROP TABLE IF EXISTS Scenario;
DROP TABLE IF EXISTS Topic;

-- Drop user subclass tables
DROP TABLE IF EXISTS Admin;
DROP TABLE IF EXISTS Mentor;
DROP TABLE IF EXISTS Student;

-- Finally drop the USER superclass table
DROP TABLE IF EXISTS User;