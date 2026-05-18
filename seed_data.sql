-- Мұғалімдерді қосу (Құпия сөз: 123456)
INSERT INTO users (email, password, full_name, role, enabled, created_at) VALUES
('teacher1@proktor.kz', '$2a$10$dXJ3SW6G7P50lGmMkkmwe.20cQQubK3.HCGFvrFsWYSceO.1Y2u.S', 'Самат Оспанов', 'TEACHER', true, NOW()),
('teacher2@proktor.kz', '$2a$10$dXJ3SW6G7P50lGmMkkmwe.20cQQubK3.HCGFvrFsWYSceO.1Y2u.S', 'Айжан Нұрланқызы', 'TEACHER', true, NOW()),
('teacher3@proktor.kz', '$2a$10$dXJ3SW6G7P50lGmMkkmwe.20cQQubK3.HCGFvrFsWYSceO.1Y2u.S', 'Ерлан Амангелді', 'TEACHER', true, NOW())
ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name;

-- Топтарды қосу
INSERT INTO student_groups (name, created_at) VALUES
('IT-2101', NOW()),
('CS-2204', NOW()),
('SE-2002', NOW()),
('IS-2305', NOW())
ON CONFLICT (name) DO NOTHING;

-- Топқа кірмеген студенттер (Құпия сөз: 123456)
INSERT INTO users (email, password, full_name, role, enabled, created_at) VALUES
('student1@proktor.kz', '$2a$10$dXJ3SW6G7P50lGmMkkmwe.20cQQubK3.HCGFvrFsWYSceO.1Y2u.S', 'Азамат Серіков', 'STUDENT', true, NOW()),
('student2@proktor.kz', '$2a$10$dXJ3SW6G7P50lGmMkkmwe.20cQQubK3.HCGFvrFsWYSceO.1Y2u.S', 'Динара Қалиева', 'STUDENT', true, NOW()),
('student3@proktor.kz', '$2a$10$dXJ3SW6G7P50lGmMkkmwe.20cQQubK3.HCGFvrFsWYSceO.1Y2u.S', 'Берік Мақсатұлы', 'STUDENT', true, NOW()),
('student4@proktor.kz', '$2a$10$dXJ3SW6G7P50lGmMkkmwe.20cQQubK3.HCGFvrFsWYSceO.1Y2u.S', 'Гүлназ Болатқызы', 'STUDENT', true, NOW()),
('student5@proktor.kz', '$2a$10$dXJ3SW6G7P50lGmMkkmwe.20cQQubK3.HCGFvrFsWYSceO.1Y2u.S', 'Руслан Омаров', 'STUDENT', true, NOW())
ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name;
