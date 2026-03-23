-- SQL Buddy: PostgreSQL Seed Data
-- "user" 需要双引号（保留字），其余表名小写无引号

-- 清空所有表，注意顺序和 "user" 的双引号
TRUNCATE TABLE receive, send, access, resourcetopic, have_topic,
               attempt, notification, resource, problem, scenario,
               topic, admin, mentor, student, "user"
RESTART IDENTITY CASCADE;

-- Users（"user" 是保留字，必须加双引号）
INSERT INTO "user" (name, email, password) VALUES
('Pizza Lover McGee',        'pizza4life@email.com',        '$2b$12$placeholder_hash_1'),
('Captain Capslock',         'YELLING@email.com',            '$2b$12$placeholder_hash_2'),
('404 Name Not Found',       'wherami@email.com',            '$2b$12$placeholder_hash_3'),
('Ctrl Alt Elite',           'hackerman@email.com',          '$2b$12$placeholder_hash_4'),
('Query McQueryface',        'selectstar@email.com',         '$2b$12$placeholder_hash_5'),
('Null Pointer Exception',   'segfault@email.com',           '$2b$12$placeholder_hash_6'),
('Syntax Error Sarah',       'missing.semicolon@email.com',  '$2b$12$placeholder_hash_7'),
('Bob Tables',               'little.bobby.tables@email.com','$2b$12$placeholder_hash_8'),
('Stack Overflow Steve',     'copypaste@email.com',          '$2b$12$placeholder_hash_9'),
('Caffeine Dependency',      'coffee.addict@email.com',      '$2b$12$placeholder_hash_10'),
('Procrastination Pro',      'do.it.later@email.com',        '$2b$12$placeholder_hash_11'),
('Meme Lord Marcus',         'dank.memes@email.com',         '$2b$12$placeholder_hash_12'),
('Binary Betty',             '01010011@email.com',           '$2b$12$placeholder_hash_13'),
('Infinite Loop Larry',      'while.true@email.com',         '$2b$12$placeholder_hash_14'),
('Cache Miss Cathy',         'slow.load@email.com',          '$2b$12$placeholder_hash_15'),
('Debug Dan',                'print.everything@email.com',   '$2b$12$placeholder_hash_16'),
('Git Commit Greg',          'push.force@email.com',         '$2b$12$placeholder_hash_17'),
('API Rate Limited Rita',    'too.many.requests@email.com',  '$2b$12$placeholder_hash_18'),
('Tabs vs Spaces Tom',       'four.spaces@email.com',        '$2b$12$placeholder_hash_19'),
('Sudo Make Me Sandwich',    'root.access@email.com',        '$2b$12$placeholder_hash_20'),
('JSON Jason',               'curly.braces@email.com',       '$2b$12$placeholder_hash_21'),
('HTML Harry',               'div.soup@email.com',           '$2b$12$placeholder_hash_22');

INSERT INTO student (user_id, enrollment_date) VALUES
(1,'2024-04-01'),(2,'2024-02-29'),(3,'2024-01-01'),(4,'2024-03-14'),
(5,'2024-05-04'),(6,'2024-10-31'),(7,'2024-12-25'),(8,'2024-07-04');

INSERT INTO mentor (user_id, expertise_area) VALUES
(9,  'Copy-Pasting from Stack Overflow'),
(10, 'Turning It Off and On Again'),
(11, 'Blaming It on Cache'),
(13, 'Googling Error Messages'),
(14, 'Writing TODO Comments'),
(15, 'Explaining to Rubber Ducks'),
(16, 'Pretending to Understand Regex');

INSERT INTO admin (user_id, admin_level) VALUES
(12,'Super'),(17,'Standard'),(18,'Super'),(19,'Standard'),
(20,'Super'),(21,'Standard'),(22,'Super');

INSERT INTO topic (topic_name, description) VALUES
('SELECT Basics',      'The art of asking nicely for data'),
('JOIN Operations',    'Making tables hold hands and play nice'),
('Aggregate Functions','Counting beans with style'),
('Subqueries',         'Queries within queries - Inception style'),
('Window Functions',   'Looking through database windows without breaking them'),
('Data Modification',  'Teaching data who is boss'),
('Database Design',    'Playing Tetris with tables'),
('Indexes',            'Making databases go vroom vroom'),
('Transactions',       'All or nothing - no take backs'),
('Views and CTEs',     'Smoke and mirrors for data');

INSERT INTO scenario (student_id, scenario_description) VALUES
(1,'Zombie Apocalypse Survival Database'),
(2,'Intergalactic Cat Cafe'),
(3,'Time Travelers Anonymous'),
(4,'Underwater Unicorn Sanctuary'),
(5,'Ninja Retirement Home'),
(1,'Wizard Tech Support'),
(6,'Dinosaur Dating App'),
(2,'Robot Therapy Sessions');

INSERT INTO problem (user_id, correct_answer, title, difficulty, scenario_no, description) VALUES
(9,  'SELECT * FROM zombies WHERE hunger_level > 9000;',                                                              'Find Hangry Zombies',          'Easy',   1, 'Locate zombies who skipped breakfast'),
(9,  'SELECT name, color FROM space_cats WHERE planet = ''Meowcury'';',                                               'Meowcury Residents',           'Easy',   2, 'Find cats living on the planet Meowcury'),
(10, 'SELECT t.name, p.incident FROM time_travelers t JOIN paradoxes p ON t.id = p.traveler_id;',                     'Match Travelers to Paradoxes', 'Medium', 3, 'Link time travelers to the chaos they caused'),
(10, 'SELECT COUNT(*) FROM unicorns WHERE rainbow_intensity = ''maximum'';',                                          'Count Max Rainbow Unicorns',   'Easy',   4, 'How many unicorns are at peak fabulousness?'),
(11, 'SELECT ninja_id, AVG(stealth_score) FROM activities GROUP BY ninja_id HAVING AVG(stealth_score) > 95;',         'Master Ninjas',                'Medium', 5, 'Find ninjas who are basically invisible'),
(9,  'SELECT w.wizard_name, (SELECT COUNT(*) FROM bugs WHERE spell_id = w.spell_id) FROM wizards w;',                'Count Spell Bugs',             'Medium', 6, 'How many bugs in each wizard spell?'),
(10, 'SELECT d.name, SUM(m.swipes) FROM dinosaurs d LEFT JOIN matches m ON d.id = m.dino_id GROUP BY d.id, d.name;', 'Dinosaur Dating Stats',        'Hard',   7, 'Who is the most popular dinosaur?'),
(11, 'SELECT * FROM robots WHERE last_therapy < NOW() - INTERVAL ''1 week'';',                                       'Robots Needing Therapy',       'Easy',   8, 'Find robots having a tough week'),
(9,  'INSERT INTO weapons (name, damage) VALUES (''Rubber Chicken'', 5);',                                            'Add Absurd Weapon',            'Easy',   1, 'Add the legendary rubber chicken to arsenal'),
(10, 'SELECT cat_name, COUNT(*) FROM cosmic_treats GROUP BY cat_id, cat_name ORDER BY count DESC LIMIT 3;',          'Top 3 Treat Hoarders',         'Hard',   2, 'Which space cats ate the most treats?');

INSERT INTO attempt (student_id, problem_id, attempt_no, mentor_id, score, feedback) VALUES
(1,1,1,NULL,96.00,NULL),
(1,2,1,9,87.00,'Good! But you forgot to ORDER BY cuteness'),
(1,3,1,NULL,69.00,NULL),
(1,3,2,10,84.00,'Much better! Time paradox avoided!'),
(1,4,1,NULL,92.00,NULL),
(2,1,1,NULL,42.00,NULL),
(2,2,1,9,88.00,'STOP YELLING IN YOUR SQL QUERIES'),
(2,4,1,NULL,99.00,NULL),
(2,5,1,11,73.00,'Ninjas would be disappointed. Try harder.'),
(2,5,2,11,91.00,'Now you are basically invisible too!'),
(3,1,1,NULL,44.04,NULL),
(3,2,1,NULL,77.77,NULL),
(3,3,1,10,66.60,'Almost evil... but not quite'),
(3,6,1,NULL,80.08,NULL),
(4,1,1,NULL,31.41,NULL),
(4,4,1,NULL,95.00,NULL),
(4,5,1,11,82.00,'Excellent stealth skills!'),
(4,7,1,NULL,74.00,NULL),
(5,2,1,NULL,75.00,NULL),
(5,3,1,10,85.00,'Your query is almost as beautiful as a sunset'),
(5,6,1,9,78.00,'Have you tried using magic wands instead of indexes?'),
(5,8,1,NULL,90.00,NULL),
(6,4,1,NULL,88.00,NULL),
(6,9,1,9,94.00,'That rubber chicken will save humanity!'),
(7,2,1,NULL,79.00,NULL),
(7,3,1,NULL,71.00,NULL),
(7,5,1,11,87.00,'You remembered the semicolon this time!'),
(8,1,1,NULL,100.00,NULL),
(8,2,1,9,13.37,'LEET SCORE! You are truly elite'),
(8,10,1,10,89.00,'Those cats deserve all the treats');

INSERT INTO resource (user_id, title, res_type, resource_url) VALUES
(9,  'How to SELECT Without Crying',             'Article',       'https://sqlbuddy.com/no-tears-guide'),
(9,  'JOIN or Die: A Historical Perspective',    'Tutorial',      'https://sqlbuddy.com/revolutionary-joins'),
(10, 'COUNT Your Blessings (and Rows)',          'Video',         'https://sqlbuddy.com/grateful-aggregates'),
(10, 'Subqueries: Going Deeper',                 'Article',       'https://sqlbuddy.com/office-reference'),
(11, 'Window Functions for the Curious',         'Tutorial',      'https://sqlbuddy.com/ethical-peeping'),
(9,  'Database Design: Not Just Playing God',    'Documentation', 'https://sqlbuddy.com/power-trip'),
(10, 'Indexes: The Fast and The Furious',        'Article',       'https://sqlbuddy.com/tokyo-drift-queries'),
(11, 'Transactions: No Ragrets Edition',         'Video',         'https://sqlbuddy.com/bad-tattoos'),
(9,  'INSERT UPDATE DELETE: Choose Your Weapon', 'Exercise',      'https://sqlbuddy.com/mortal-kombat-sql'),
(10, 'Views and CTEs: Now You See Me',           'Tutorial',      'https://sqlbuddy.com/magic-tricks');

INSERT INTO notification (send_time) VALUES
(NOW() - INTERVAL '42 days'),
(NOW() - INTERVAL '404 hours'),
(NOW() - INTERVAL '1337 minutes'),
(NOW() - INTERVAL '69 days'),
(NOW() - INTERVAL '13 hours'),
(NOW() - INTERVAL '7 days'),
(NOW() - INTERVAL '3 days'),
(NOW() - INTERVAL '666 minutes'),
(NOW() - INTERVAL '8 hours'),
(NOW() - INTERVAL '2 hours');

INSERT INTO have_topic VALUES
(1,'SELECT Basics'),(2,'SELECT Basics'),(3,'JOIN Operations'),
(4,'Aggregate Functions'),(5,'Aggregate Functions'),(6,'Subqueries'),
(7,'JOIN Operations'),(7,'Aggregate Functions'),(8,'SELECT Basics'),
(9,'Data Modification'),(10,'Aggregate Functions');

INSERT INTO resourcetopic VALUES
(1,'SELECT Basics'),(2,'JOIN Operations'),(3,'Aggregate Functions'),
(4,'Subqueries'),(5,'Window Functions'),(6,'Database Design'),
(7,'Indexes'),(8,'Transactions'),(9,'Data Modification'),(10,'Views and CTEs');

INSERT INTO access VALUES
(1,1),(2,1),(3,1),(1,2),(3,2),(1,3),(4,3),(5,3),
(5,4),(6,4),(6,5),(7,5),(7,6),(8,6),(9,7),(10,7),(1,8),(10,8);

INSERT INTO send VALUES
(12,1),(12,2),(9,3),(12,4),(10,5),(12,6),(12,7),(11,8),(12,9),(12,10);