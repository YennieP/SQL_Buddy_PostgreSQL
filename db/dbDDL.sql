-- SQL Buddy: PostgreSQL DDL
-- 注意：user 是 PostgreSQL 保留字，必须用双引号 "user"
-- 其余表名全部小写无引号

CREATE TABLE IF NOT EXISTS "user" (
    user_id     SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(150) UNIQUE NOT NULL,
    password    VARCHAR(255) NOT NULL,
    status      VARCHAR(10) DEFAULT 'active',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_email ON "user" (email);

CREATE TABLE IF NOT EXISTS student (
    user_id                  INT PRIMARY KEY REFERENCES "user"(user_id) ON DELETE CASCADE,
    enrollment_date          DATE DEFAULT CURRENT_DATE,
    total_problems_attempted INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS mentor (
    user_id          INT PRIMARY KEY REFERENCES "user"(user_id) ON DELETE CASCADE,
    expertise_area   VARCHAR(100),
    problems_created INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS admin (
    user_id     INT PRIMARY KEY REFERENCES "user"(user_id) ON DELETE CASCADE,
    admin_level VARCHAR(10) DEFAULT 'Standard' CHECK (admin_level IN ('Super', 'Standard'))
);

CREATE TABLE IF NOT EXISTS topic (
    topic_name  VARCHAR(100) PRIMARY KEY,
    description TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scenario (
    scenario_no          SERIAL PRIMARY KEY,
    student_id           INT NOT NULL REFERENCES student(user_id) ON DELETE CASCADE,
    scenario_description TEXT NOT NULL,
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_student_scenario ON scenario (student_id);

CREATE TABLE IF NOT EXISTS problem (
    problem_id     SERIAL PRIMARY KEY,
    user_id        INT NOT NULL REFERENCES mentor(user_id) ON DELETE CASCADE,
    correct_answer TEXT NOT NULL,
    create_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    title          VARCHAR(200) NOT NULL,
    difficulty     VARCHAR(6) NOT NULL CHECK (difficulty IN ('Easy', 'Medium', 'Hard')),
    scenario_no    INT REFERENCES scenario(scenario_no) ON DELETE SET NULL,
    description    TEXT
);
CREATE INDEX IF NOT EXISTS idx_difficulty ON problem (difficulty);
CREATE INDEX IF NOT EXISTS idx_mentor     ON problem (user_id);

CREATE TABLE IF NOT EXISTS attempt (
    student_id  INT REFERENCES student(user_id) ON DELETE CASCADE,
    problem_id  INT REFERENCES problem(problem_id) ON DELETE CASCADE,
    attempt_no  INT NOT NULL,
    mentor_id   INT REFERENCES mentor(user_id) ON DELETE SET NULL,
    score       DECIMAL(5,2) CHECK (score >= 0 AND score <= 100),
    submit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    feedback    TEXT,
    PRIMARY KEY (student_id, problem_id, attempt_no)
);
CREATE INDEX IF NOT EXISTS idx_student_attempts ON attempt (student_id);
CREATE INDEX IF NOT EXISTS idx_problem_attempts ON attempt (problem_id);

CREATE TABLE IF NOT EXISTS resource (
    resource_id   SERIAL PRIMARY KEY,
    user_id       INT NOT NULL REFERENCES mentor(user_id) ON DELETE CASCADE,
    title         VARCHAR(200) NOT NULL,
    res_type      VARCHAR(15) NOT NULL CHECK (res_type IN ('Article','Video','Tutorial','Documentation','Exercise')),
    uploaded_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resource_url  VARCHAR(500)
);
CREATE INDEX IF NOT EXISTS idx_resource_type ON resource (res_type);

CREATE TABLE IF NOT EXISTS notification (
    noti_id   SERIAL PRIMARY KEY,
    send_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS have_topic (
    problem_id INT REFERENCES problem(problem_id) ON DELETE CASCADE,
    topic_name VARCHAR(100) REFERENCES topic(topic_name) ON DELETE CASCADE,
    PRIMARY KEY (problem_id, topic_name)
);

CREATE TABLE IF NOT EXISTS resourcetopic (
    resource_id INT REFERENCES resource(resource_id) ON DELETE CASCADE,
    topic_name  VARCHAR(100) REFERENCES topic(topic_name) ON DELETE CASCADE,
    PRIMARY KEY (resource_id, topic_name)
);

CREATE TABLE IF NOT EXISTS access (
    resource_id INT REFERENCES resource(resource_id) ON DELETE CASCADE,
    student_id  INT REFERENCES student(user_id) ON DELETE CASCADE,
    access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (resource_id, student_id)
);

CREATE TABLE IF NOT EXISTS send (
    sender_id INT REFERENCES "user"(user_id) ON DELETE CASCADE,
    noti_id   INT REFERENCES notification(noti_id) ON DELETE CASCADE,
    PRIMARY KEY (sender_id, noti_id)
);

CREATE TABLE IF NOT EXISTS receive (
    receiver_id INT REFERENCES "user"(user_id) ON DELETE CASCADE,
    noti_id     INT REFERENCES notification(noti_id) ON DELETE CASCADE,
    PRIMARY KEY (receiver_id, noti_id)
);

-- VIEWS

CREATE OR REPLACE VIEW studentperformancesummary AS
SELECT
    s.user_id,
    u.name,
    u.email,
    COUNT(DISTINCT a.problem_id) AS problems_attempted,
    AVG(a.score)                 AS average_score,
    MAX(a.score)                 AS highest_score,
    COUNT(a.attempt_no)          AS total_attempts
FROM student s
JOIN "user" u ON s.user_id = u.user_id
LEFT JOIN attempt a ON s.user_id = a.student_id
GROUP BY s.user_id, u.name, u.email;

CREATE OR REPLACE VIEW problemstatistics AS
SELECT
    p.problem_id,
    p.title,
    p.difficulty,
    STRING_AGG(DISTINCT ht.topic_name, ',') AS topics,
    COUNT(DISTINCT a.student_id)            AS students_attempted,
    AVG(a.score)                            AS average_score,
    COUNT(a.attempt_no)                     AS total_attempts,
    u.name                                  AS created_by_mentor
FROM problem p
LEFT JOIN attempt a     ON p.problem_id = a.problem_id
LEFT JOIN have_topic ht ON p.problem_id = ht.problem_id
LEFT JOIN "user" u      ON p.user_id    = u.user_id
GROUP BY p.problem_id, p.title, p.difficulty, u.name;

CREATE OR REPLACE VIEW mentoractivitydashboard AS
SELECT
    m.user_id,
    u.name                        AS mentor_name,
    COUNT(DISTINCT p.problem_id)  AS problems_created,
    COUNT(DISTINCT r.resource_id) AS resources_uploaded,
    COUNT(DISTINCT a.student_id)  AS students_mentored,
    AVG(a.score)                  AS avg_student_score
FROM mentor m
JOIN "user" u        ON m.user_id = u.user_id
LEFT JOIN problem p  ON m.user_id = p.user_id
LEFT JOIN resource r ON m.user_id = r.user_id
LEFT JOIN attempt a  ON m.user_id = a.mentor_id
GROUP BY m.user_id, u.name;

-- TRIGGERS

CREATE OR REPLACE FUNCTION check_mentor_feedback()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.mentor_id IS NOT NULL AND NEW.feedback IS NULL THEN
        RAISE EXCEPTION 'Feedback is required when mentor_id is provided';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS before_attempt_insert ON attempt;
CREATE TRIGGER before_attempt_insert
    BEFORE INSERT ON attempt
    FOR EACH ROW EXECUTE FUNCTION check_mentor_feedback();

DROP TRIGGER IF EXISTS before_attempt_update ON attempt;
CREATE TRIGGER before_attempt_update
    BEFORE UPDATE ON attempt
    FOR EACH ROW EXECUTE FUNCTION check_mentor_feedback();

CREATE OR REPLACE FUNCTION increment_mentor_problems()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE mentor SET problems_created = problems_created + 1
    WHERE user_id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS after_problem_insert ON problem;
CREATE TRIGGER after_problem_insert
    AFTER INSERT ON problem
    FOR EACH ROW EXECUTE FUNCTION increment_mentor_problems();

CREATE OR REPLACE FUNCTION notify_high_score()
RETURNS TRIGGER AS $$
DECLARE v_noti_id INT;
BEGIN
    IF NEW.score >= 90 THEN
        INSERT INTO notification (send_time) VALUES (NOW())
        RETURNING noti_id INTO v_noti_id;
        INSERT INTO receive (receiver_id, noti_id) VALUES (NEW.student_id, v_noti_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS after_high_score_attempt ON attempt;
CREATE TRIGGER after_high_score_attempt
    AFTER INSERT ON attempt
    FOR EACH ROW EXECUTE FUNCTION notify_high_score();

CREATE OR REPLACE FUNCTION prevent_attempted_problem_delete()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM attempt WHERE problem_id = OLD.problem_id) THEN
        RAISE EXCEPTION 'Cannot delete problem that has been attempted by students';
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS before_problem_delete ON problem;
CREATE TRIGGER before_problem_delete
    BEFORE DELETE ON problem
    FOR EACH ROW EXECUTE FUNCTION prevent_attempted_problem_delete();