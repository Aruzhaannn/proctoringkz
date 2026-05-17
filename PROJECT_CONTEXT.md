# ProctorAI — Полный Контекст Проекта
> **Последнее обновление:** 2026-05-18  
> **Автор проекта:** Қожахметова Аружан  
> **Назначение файла:** Этот файл содержит **полное описание проекта** для AI-агентов. Прочитайте его ВМЕСТО повторного анализа всех файлов.

---

## 1. Обзор проекта

**ProctorAI** — платформа AI-прокторинга для университетских онлайн-экзаменов. Система отслеживает студентов во время экзамена через камеру, микрофон и мониторинг действий в браузере, вычисляя "cheat score" (0–100%).

**Язык интерфейса:** Казахский (kk)

---

## 2. Архитектура (Микросервисы + Docker + K8s)

```
┌───────────────────────────────────────────────────────┐
│  Frontend (Vanilla HTML/CSS/JS — Nginx)  :80          │
└──────────┬─────────────────────┬──────────────────────┘
           │ /api/*              │ /ai/*
           ▼                     ▼
┌──────────────────┐   ┌──────────────────┐
│ Backend (Java)   │   │ AI Service       │
│ Spring Boot 3.3  │   │ Python/FastAPI   │
│ :8080 → :9090    │   │ :8000            │
└──────┬───────────┘   └──────────────────┘
       │
  ┌────┼─────────────────────┐
  ▼    ▼                     ▼
┌─────────┐  ┌──────────┐  ┌──────────┐
│Postgres │  │  Redis   │  │  Kafka   │
│  :5432  │  │  :6379   │  │  :9092   │
└─────────┘  └──────────┘  └──────────┘
```

**Docker Compose** управляет всеми сервисами. **K8s** манифесты лежат в `/k8s/`.

---

## 3. Структура файлов

```
proctoringkz/
├── docker-compose.yml            # Оркестрация: postgres, redis, kafka, backend, ai-service, frontend
├── docker-compose.simple.yml     # Упрощённый (без Kafka, Analytics)
├── start-dev.bat                 # Сборка и запуск всех контейнеров (Windows)
├── stop-dev.bat                  # Остановка контейнеров
├── PROJECT_CONTEXT.md            # ← ЭТОТ ФАЙЛ
│
├── backend/                      # Java Spring Boot 3.3.0, Java 21
│   ├── pom.xml                   # Maven, зависимости: spring-web, security, jpa, redis, kafka, jwt, actuator, lombok
│   ├── Dockerfile                # Multi-stage: eclipse-temurin:21-jdk → 21-jre
│   ├── mvnw / mvnw.cmd
│   └── src/main/
│       ├── resources/
│       │   └── application.yml   # Конфигурация (postgres, redis, kafka, jwt)
│       └── java/kz/proktorai/
│           ├── ProktorAiApplication.java
│           ├── config/
│           │   ├── SecurityConfig.java       # JWT stateless, CORS, BCrypt
│           │   ├── DataInitializer.java       # Создаёт demo-пользователей при запуске
│           │   ├── CacheConfig.java           # Redis cache manager
│           │   └── KafkaConfig.java           # Kafka topics auto-creation
│           ├── controller/
│           │   ├── AuthController.java        # /api/v1/auth/*
│           │   ├── ExamController.java        # /api/v1/exams/*
│           │   ├── ExamSessionController.java # /api/v1/sessions/*
│           │   └── AuditLogController.java    # /api/v1/audit/*
│           ├── dto/
│           │   ├── LoginRequest.java          # email, password
│           │   ├── RegisterRequest.java       # email, password, fullName, role
│           │   ├── AuthResponse.java          # accessToken, refreshToken, userId, email, fullName, role
│           │   ├── AuditLogRequest.java
│           │   ├── AuditLogResponse.java
│           │   └── exam/
│           │       ├── ExamRequest.java        # title, description, durationMinutes
│           │       ├── ExamResponse.java       # id, title, description, duration, status, createdByName, startTime, endTime
│           │       ├── SessionResponse.java    # id, examId, examTitle, studentId, studentName, status, cheatScore, violations[]
│           │       ├── ViolationRequest.java   # sessionId, type, score, details
│           │       └── ViolationResponse.java  # id, type, score, details, detectedAt
│           ├── entity/
│           │   ├── User.java           # implements UserDetails; fields: id, email, password, fullName, role, enabled, createdAt
│           │   ├── Role.java           # enum: STUDENT, TEACHER, ADMIN
│           │   ├── Exam.java           # fields: id, title, description, durationMinutes, startTime, endTime, status, createdBy(User)
│           │   ├── ExamStatus.java     # enum: DRAFT, ACTIVE, FINISHED
│           │   ├── ExamSession.java    # fields: id, exam, student, startTime, endTime, status, cheatScore, phoneUnlocked, violations[]
│           │   ├── SessionStatus.java  # enum: IN_PROGRESS, COMPLETED, TERMINATED
│           │   └── Violation.java      # fields: id, examSession, type, score, details, detectedAt
│           ├── repository/
│           │   ├── UserRepository.java
│           │   ├── ExamRepository.java
│           │   ├── ExamSessionRepository.java
│           │   ├── ViolationRepository.java
│           │   └── AuditLogRepository.java
│           ├── service/
│           │   ├── AuthService.java           # register, login, refreshToken
│           │   ├── ExamService.java           # create, activate, finish, getActive, getByTeacher, getById, getAll
│           │   └── ExamSessionService.java    # startSession, finishSession, terminateSession, phoneUnlock/Lock, addViolation, getMy, getByExam
│           ├── security/
│           │   ├── JwtTokenProvider.java       # Генерация/валидация JWT (JJWT 0.12.6)
│           │   ├── JwtAuthFilter.java          # OncePerRequestFilter
│           │   └── UserDetailsServiceImpl.java # Загрузка пользователя из БД
│           └── kafka/
│               ├── ViolationEvent.java     # sessionId, violationType, score, details
│               ├── ViolationProducer.java   # Отправка ViolationEvent в Kafka topic
│               ├── ViolationConsumer.java   # Получение ViolationEvent из Kafka
│               ├── SessionEvent.java        # sessionId, studentName, examTitle, status, cheatScore
│               ├── SessionProducer.java     # Отправка SessionEvent
│               └── SessionConsumer.java     # Получение SessionEvent
│
├── ai-service/                   # Python FastAPI + MediaPipe + YOLOv8
│   ├── Dockerfile                # python:3.11-slim
│   ├── requirements.txt          # fastapi, uvicorn, opencv, mediapipe==0.10.14, numpy<2.0.0, ultralytics(YOLOv8)
│   ├── yolov8n.pt                # Предобученная модель YOLOv8 nano
│   ├── face_detection_test.py
│   └── app/
│       ├── main.py               # FastAPI app, CORS, /health endpoint
│       ├── models/
│       │   └── schemas.py        # Pydantic модели
│       ├── routers/
│       │   └── analyze.py        # POST /api/v1/analyze (frame), POST /api/v1/analyze/audio
│       └── services/
│           ├── face_detector.py       # MediaPipe Face Detection + FaceMesh (478 landmarks, max 5 faces)
│           ├── gaze_analyzer.py       # Iris-based gaze (landmarks 468-477: left/right/up/down/diagonal)
│           ├── head_pose_estimator.py # solvePnP head pose from FaceMesh (pitch/yaw/roll, порог 20°)
│           ├── object_detector.py     # YOLOv8 (conf=0.25 для телефонов, conf=0.45 для людей)
│           └── audio_detector.py      # Анализ аудио (librosa, VAD)
│
├── proktorai-kz/                 # Фронтенд — статический HTML/CSS/JS
│   ├── Dockerfile                # nginx:alpine
│   ├── nginx.conf                # Proxy: /api/→backend:8080, /ai/→ai-service:8000
│   ├── index.html                # Страница входа (Login) с демо-данными
│   ├── css/
│   │   ├── global.css            # Глобальные стили, дизайн-система, dark theme
│   │   └── login.css             # Стили страницы входа
│   ├── js/
│   │   ├── api.js                # API-клиент: Auth, AuthAPI, ExamAPI, SessionAPI, AiAPI + auto-detect docker/local
│   │   ├── login.js              # Логика входа с ролями
│   │   ├── cheating-engine.js    # Клиентский движок обнаружения нарушений
│   │   ├── evidence-collector.js # Сборщик доказательств нарушений
│   │   └── theme.js              # Переключатель тем
│   └── pages/
│       ├── student-dashboard.html   # Панель студента (мои экзамены, сессии, статистика)
│       ├── teacher-dashboard.html   # Панель преподавателя (мониторинг, создание экзаменов, живые оповещения)
│       ├── admin-dashboard.html     # Панель администратора (пользователи, сервисы, аудит, архитектура, финансы)
│       └── exam-room.html           # Экзаменационная комната (WebRTC камера, прокторинг, таймер, вопросы)
│
├── k8s/                          # Kubernetes манифесты
│   ├── namespace.yml
│   ├── secrets.yml
│   ├── postgres.yml
│   ├── redis.yml
│   ├── kafka.yml
│   ├── backend.yml
│   ├── ai-service.yml
│   ├── frontend.yml
│   ├── analytics-service.yml
│   └── deploy.sh
│
└── .github/workflows/
    ├── ci.yml                    # CI: lint, test, build
    └── cd.yml                    # CD: deploy
```

---

## 4. REST API Endpoints

### Auth (`/api/v1/auth`)
| Method | Path        | Auth | Description |
|--------|-------------|------|-------------|
| POST   | /register   | ❌   | Регистрация (email, password, fullName, role) |
| POST   | /login      | ❌   | Вход → {accessToken, refreshToken, userId, email, fullName, role} |
| POST   | /refresh    | ❌   | Обновление токена |
| GET    | /me         | ✅   | Данные текущего пользователя |

### Exams (`/api/v1/exams`)
| Method | Path           | Role          | Description |
|--------|----------------|---------------|-------------|
| POST   | /              | TEACHER,ADMIN | Создать экзамен |
| PATCH  | /{id}/activate | TEACHER,ADMIN | Активировать экзамен |
| PATCH  | /{id}/finish   | TEACHER,ADMIN | Завершить экзамен |
| GET    | /active        | Any auth      | Список активных экзаменов |
| GET    | /my            | TEACHER,ADMIN | Мои экзамены |
| GET    | /{id}          | Any auth      | Экзамен по ID |
| GET    | /              | ADMIN         | Все экзамены |

### Sessions (`/api/v1/sessions`)
| Method | Path               | Role          | Description |
|--------|--------------------|---------------|-------------|
| POST   | /start/{examId}    | STUDENT       | Начать экзамен |
| PATCH  | /{id}/finish       | STUDENT       | Завершить экзамен |
| PATCH  | /{id}/terminate    | TEACHER,ADMIN | Принудительно остановить |
| PATCH  | /{id}/phone-unlock | TEACHER,ADMIN | Разблокировать телефон |
| PATCH  | /{id}/phone-lock   | TEACHER,ADMIN | Заблокировать телефон |
| POST   | /violations        | Any auth      | Добавить нарушение (от AI) |
| GET    | /my                | STUDENT       | Мои сессии |
| GET    | /exam/{examId}     | TEACHER,ADMIN | Сессии экзамена |
| GET    | /{id}              | Any auth      | Сессия по ID |
| GET    | /{id}/violations   | TEACHER,ADMIN | Нарушения сессии |

### AI Service (`/api/v1`)
| Method | Path            | Description |
|--------|-----------------|-------------|
| POST   | /analyze        | Анализ кадра камеры (multipart: session_id, frame, tab_switches, copy_paste_count, window_minimized) |
| POST   | /analyze/audio  | Анализ аудио (multipart: session_id, audio) |
| GET    | /health         | Healthcheck |

---

## 5. База данных (PostgreSQL)

### Таблицы (DDL auto: `update`)
```
users
├── id (BIGSERIAL PK)
├── email (VARCHAR UNIQUE NOT NULL)
├── password (VARCHAR NOT NULL)          -- BCrypt
├── full_name (VARCHAR NOT NULL)
├── role (VARCHAR NOT NULL)              -- STUDENT | TEACHER | ADMIN
├── enabled (BOOLEAN DEFAULT true)
└── created_at (TIMESTAMP NOT NULL)

exams
├── id (BIGSERIAL PK)
├── title (VARCHAR NOT NULL)
├── description (TEXT)
├── duration_minutes (INT NOT NULL)
├── start_time (TIMESTAMP)
├── end_time (TIMESTAMP)
├── status (VARCHAR NOT NULL)            -- DRAFT | ACTIVE | FINISHED
├── created_by (BIGINT FK → users.id)
└── created_at (TIMESTAMP NOT NULL)

exam_sessions
├── id (BIGSERIAL PK)
├── exam_id (BIGINT FK → exams.id)
├── student_id (BIGINT FK → users.id)
├── start_time (TIMESTAMP NOT NULL)
├── end_time (TIMESTAMP)
├── status (VARCHAR NOT NULL)            -- IN_PROGRESS | COMPLETED | TERMINATED
├── cheat_score (INT DEFAULT 0)
└── phone_unlocked (BOOLEAN DEFAULT false)

violations
├── id (BIGSERIAL PK)
├── session_id (BIGINT FK → exam_sessions.id)
├── type (VARCHAR NOT NULL)              -- NO_FACE, PHONE_DETECTED, HEAD_TURNED, GAZE_AWAY, etc.
├── score (INT NOT NULL)                 -- Вес нарушения
├── details (TEXT)                       -- JSON от AI
└── detected_at (TIMESTAMP NOT NULL)
```

---

## 6. Демо-данные (DataInitializer)

При первом запуске автоматически создаются:
| Email             | Пароль  | Роль    | Имя             |
|-------------------|---------|---------|-----------------|
| student@demo.kz   | demo123 | STUDENT | Айгерім Студент |
| teacher@demo.kz   | demo123 | TEACHER | Алмас Оқытушы   |
| admin@demo.kz     | demo123 | ADMIN   | Нұрлан Әкімші   |

---

## 7. Конфигурация (application.yml)

```yaml
spring.datasource.url:      jdbc:postgresql://localhost:5432/proctoring_db
spring.datasource.username:  postgres
spring.datasource.password:  1234
spring.data.redis.host:      localhost:6379
spring.kafka.bootstrap:      localhost:9092
server.port:                 8080
app.jwt.secret:              404E63526655...  (hex)
app.jwt.expiration:          86400000 (24ч)
app.jwt.refresh-expiration:  604800000 (7 дней)
kafka.topics:                proktorai.violations, proktorai.sessions
```

---

## 8. Frontend — API клиент (api.js)

```javascript
// Авто-определение среды
const IS_DOCKER = window.location.port === '80' || window.location.port === '';
const API_BASE  = IS_DOCKER ? '/api/v1' : 'http://localhost:8080/api/v1';
const AI_BASE   = IS_DOCKER ? '/ai'     : 'http://localhost:8000/api/v1';

// Объекты:
Auth     — save(data), token(), user(), role(), clear(), check()
AuthAPI  — login(email, pwd), register(data), me()
ExamAPI  — getActive(), getById(id), getMine(), create(data), activate(id), finish(id)
SessionAPI — start(examId), finish(id), getMy(), getByExam(examId), addViolation(data)
AiAPI    — analyzeFrame(sessionId, blob, counters), analyzeAudio(sessionId, blob)
```

---

## 9. Экзаменационная комната (exam-room.html)

Ключевые возможности:
- **WebRTC камера** — getUserMedia (видео + аудио)
- **AI Face Detection** — MediaPipe через AI-service, рамка зелёная/красная по статусу
- **Микрофон мониторинг** — AudioContext + AnalyserNode визуализация
- **Мониторинг нарушений:**
  - Переключение вкладок (visibilitychange)
  - Ctrl+C / Ctrl+V (keydown)
  - Сворачивание окна (blur/focus)
  - Отсутствие лица / несколько лиц (AI)
  - Телефон, книга (YOLOv8)
  - Направление взгляда (iris-based)
  - Поворот головы (solvePnP)
- **Уведомления (Toasts):** Все нарушения (потеря лица, телефон, вкладки) выводятся через неблокирующие всплывающие уведомления (toasts) внизу экрана, не прерывая работу.
- **Отсутствие авто-терминации:** Система только предупреждает студента и отправляет логи/уведомления преподавателю. Решение о завершении экзамена принимает только преподаватель.
- **AI-анализ кадров:** Каждые 3 сек отправка кадра 640×480 на AI-service (работает и без backend session)
- **Таймер обратного отсчёта**

### Типы нарушений (WARNING_RULES)
```
NO_FACE, MULTIPLE_FACES, MULTIPLE_PERSONS, PERSON_ABSENT,
GAZE_AWAY, HEAD_TURNED, PHONE_DETECTED, BOOK_DETECTED,
TAB_SWITCH, COPY_PASTE, WINDOW_MINIMIZED,
MULTIPLE_VOICES, VOICE_DETECTED
```

---

## 10. Панели управления

### Student Dashboard
- Список доступных активных экзаменов
- Мои сессии с результатами
- Кнопка "Начать экзамен"

### Teacher Dashboard
- Живой мониторинг студентов (карточки — **только реальные данные из API**, без демо-данных)
- Создание/активация/завершение экзаменов
- Лента оповещений о нарушениях в реальном времени
- Рейтинг по cheat score
- Фильтрация по уровню риска (low/mid/high)
- Принудительная терминация сессии студента
- Динамическая таблица студентов (заполняется из сессий)

### Admin Dashboard
- Статистика: пользователи, экзамены, AI детекции, SLA
- Здоровье микросервисов (Auth, Exam, AI, Proctoring, Analytics, Kafka)
- Вкладки: Пользователи, Архитектура, Аудит, Управление экзаменами, **Финансы (отчёт)**
- Финансовый отчёт: общие поступления, платные пересдачи, ожидающие платежи, таблица транзакций

---

## 11. Стек технологий

| Слой         | Технологии |
|-------------|-----------|
| Frontend     | HTML5, CSS3, Vanilla JS, Google Fonts (Syne + DM Sans) |
| Backend      | Java 21, Spring Boot 3.3.0, Spring Security, Spring Data JPA, Spring Kafka |
| AI Service   | Python 3.11, FastAPI, OpenCV, **MediaPipe** (v0.10.14), **YOLOv8** (ultralytics, conf=0.25/0.45) |
| Database     | PostgreSQL 17 (Alpine) |
| Cache        | Redis 7 (Alpine) |
| Messaging    | Apache Kafka 3.7.0 |
| Auth         | JWT (JJWT 0.12.6), BCrypt |
| Container    | Docker, Docker Compose |
| Orchestration| Kubernetes (манифесты в /k8s/) |
| CI/CD        | GitHub Actions (ci.yml + cd.yml) |
| Proxy        | Nginx (проксирование /api/ и /ai/) |

---

## 12. Запуск проекта

### Вариант A: BAT-файл (Windows, рекомендуется)
```bash
# Двойной клик на start-dev.bat
# Автоматически: проверка Docker → остановка старых → сборка → запуск → healthcheck → открытие браузера
# Остановка: stop-dev.bat
```

### Вариант B: Docker Compose (ручной)
```bash
docker-compose up -d --build
# Frontend: http://localhost:80
# Backend:  http://localhost:9090
# AI:       http://localhost:8000
```

### Вариант C: Локальная разработка
```bash
# 1. PostgreSQL (Docker или локальный, порт 5432, БД: proctoring_db, user: postgres, pass: 1234)
# 2. Backend:
cd backend && ./mvnw spring-boot:run
# 3. AI Service:
cd ai-service && pip install -r requirements.txt && uvicorn app.main:app --port 8000
# 4. Frontend: просто открыть proktorai-kz/index.html в браузере (file:// или Live Server :5500)
```

### БД создаётся автоматически
PostgreSQL контейнер создаёт БД `proctoring_db` через `POSTGRES_DB`. Spring Boot создаёт таблицы через JPA `ddl-auto: update`. `DataInitializer` создаёт 3 демо-аккаунта.

### CORS и Nginx (для локальной разработки)
Разрешены origins: `http://localhost`, `http://localhost:80`, `localhost:3000`, `localhost:8080`, `localhost:9090`, `127.0.0.1:5500`, `localhost:5500`, `127.0.0.1:5173`, `localhost:5173`, `null`.
Nginx настроен с `client_max_body_size 10m` для передачи изображений с камеры.

---

## 13. Известные проблемы и заметки

1. **Lombok + Java 21 (JDK 26):** Если JDK слишком новый, Lombok может не компилироваться (`TypeTag :: UNKNOWN`). Решение — использовать Docker (eclipse-temurin:21) для сборки.
2. **Docker Desktop** должен быть запущен для `docker-compose`. Используйте `start-dev.bat`.
3. **Kafka** может долго стартовать (30+ секунд); healthcheck настроен с `start_period: 30s`.
4. **AI Service** загружает MediaPipe модели (~30 МБ) и YOLOv8 при первом запуске — задержка 30-60 сек.
5. **Frontend** работает как статические файлы (file://) для локальной разработки — api.js авто-определяет среду.
6. **Данные финансов** в admin-dashboard пока статические (hardcoded HTML), не связаны с бэкендом API.
7. **AI детекция работает без backend** — если нет sessionId, используется fallback `demo`.

---

## 14. Дизайн-система (CSS)

Файл `global.css` определяет:
- **Цвета:** `--accent: #4F8EFF`, `--accent-2: #7B5FFF`, `--accent-green: #2DD4A0`, `--accent-yellow: #F5C842`
- **Шрифты:** `--font-display: 'Syne'`, `--font-body: 'DM Sans'`
- **Тема:** Тёмная (dark mode по умолчанию)
- **Компоненты:** `.card`, `.btn`, `.badge`, `.stat-card`, `.data-table`, `.progress-bar`, `.sidebar`, `.navbar`
- **Анимации:** `.fade-in`, `.pulse-dot`, `.scanLine`
- **Layout:** `.app-layout` (sidebar + main), `.grid-2`, `.grid-3`, `.grid-4`
