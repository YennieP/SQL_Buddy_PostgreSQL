-- SQL Buddy: Database SQL Script
-- Phase IV - CS 5200 Database Project
-- Group 11: SQL Buddy

USE sqlbuddy;

/*
Q1
1.List students who have not solved any problem yet.
- LEFT JOIN
- Expected output columns
	student_id
	name
	email
	Sorted by name ascending
*/
SELECT
	s.user_id AS student_id,
	u.name,
	u.email
FROM Student s
JOIN User u
	ON u.user_id = s.user_id
LEFT JOIN Attempt a
	ON a.student_id = s.user_id
WHERE a.student_id IS NULL
ORDER BY u.name ASC;

/*
Q2
2.Retrieve all SQL problems created by a specific mentor.
- JOIN
- Expected output columns
	problem_id
	title
	difficulty
	mentor_name
	Sorted by problem_id ascending
*/
SELECT
	p.problem_id,
	p.title,
	p.difficulty,
	u.name AS mentor_name
FROM Problem p
JOIN User u
	ON u.user_id = p.user_id
WHERE u.name = 'Stack Overflow Steve'
ORDER BY p.problem_id ASC;

/*
Q3
3.Find the total number of problems per difficulty level.
- GROUP BY + HAVING + ORDER BY
- Expected output columns
	difficulty
	problem_count
	Sorted by problem_count descending then difficulty
*/
SELECT
	p.difficulty,
	COUNT(*) AS problem_count
FROM Problem p
GROUP BY p.difficulty
HAVING COUNT(*) > 0
ORDER BY problem_count DESC, p.difficulty ASC;

/*
Q4
4.Show the top 5 students with the highest average score across all attempts.
- JOIN, GROUP BY + HAVING + ORDER BY
- Expected output columns
	student_id
	student_name
	avg_score rounded to two decimals
	total_attempts
*/
SELECT
	s.user_id AS student_id,
	u.name AS student_name,
	ROUND(AVG(a.score), 2) AS avg_score,
	COUNT(*) AS total_attempts
FROM Attempt a
JOIN Student s
	ON s.user_id = a.student_id
JOIN User u
	ON u.user_id = s.user_id
GROUP BY s.user_id, u.name
HAVING COUNT(*) >= 1
ORDER BY avg_score DESC, total_attempts DESC, student_name ASC
LIMIT 5;

/*
Q5
7.For each problem, find the student with the highest score.
- JOIN, Subquery (inline view in FROM)
- Expected output columns
	problem_id
	problem_title
	student_id
	student_name
	score
	Sorted by problem_id ascending then score descending
*/
SELECT
	a.problem_id,
	p.title AS problem_title,
	a.student_id,
	u.name AS student_name,
	a.score
FROM Attempt a
JOIN (
	SELECT
		problem_id,
		MAX(score) AS max_score
	FROM Attempt
	GROUP BY problem_id
) mx
	ON mx.problem_id = a.problem_id
	AND mx.max_score = a.score
JOIN Problem p
	ON p.problem_id = a.problem_id
JOIN User u
	ON u.user_id = a.student_id
ORDER BY a.problem_id ASC, a.score DESC;

/*
Q6
9.List problems that more than 50% of students failed on their first attempt.
	A fail means score less than 60
- CTE (WITH), JOIN, GROUP BY + HAVING + ORDER BY
- Expected output columns
	problem_id
	problem_title
	failed_first_attempts
	total_students
	fail_ratio between 0 and 1
	Sorted by fail_ratio descending then problem_id
*/
WITH total AS (
	SELECT COUNT(*) AS total_students FROM Student
),
first_attempt AS (
	SELECT
		a.problem_id,
		SUM(CASE WHEN a.score < 60 THEN 1 ELSE 0 END) AS failed_first_attempts,
		COUNT(*) AS first_attempt_rows
	FROM Attempt a
	WHERE a.attempt_no = 1
	GROUP BY a.problem_id
)
SELECT
	fa.problem_id,
	p.title AS problem_title,
	fa.failed_first_attempts,
	t.total_students,
	fa.failed_first_attempts / t.total_students AS fail_ratio
FROM first_attempt fa
CROSS JOIN total t
JOIN Problem p
	ON p.problem_id = fa.problem_id
HAVING fa.failed_first_attempts > 0
	AND fa.failed_first_attempts > 0.5 * t.total_students
ORDER BY fail_ratio DESC, fa.problem_id ASC;


/*
Q7
11.Find the average score of attempts on scenario-generated problems, grouped by difficulty.
- JOIN, GROUP BY + HAVING + ORDER BY
- Expected output columns
	difficulty
	avg_score rounded to two decimals
	attempt_count
*/
SELECT
	p.difficulty,
	ROUND(AVG(a.score), 2) AS avg_score,
	COUNT(*) AS attempt_count
FROM Problem p
JOIN Attempt a
	ON a.problem_id = p.problem_id
WHERE p.scenario_no IS NOT NULL
GROUP BY p.difficulty
HAVING COUNT(*) > 0
ORDER BY avg_score DESC, p.difficulty ASC;

/*
Q8
15.Count total notifications per user.
- LEFT JOIN, GROUP BY + ORDER BY
- Expected output columns
	user_id
	name
	email
	notif_count
	Sorted by notif_count descending then name
*/
SELECT
	u.user_id,
	u.name,
	u.email,
	COUNT(r.noti_id) AS notif_count
FROM User u
LEFT JOIN Receive r
	ON r.receiver_id = u.user_id
GROUP BY u.user_id, u.name, u.email
ORDER BY notif_count DESC, u.name ASC;