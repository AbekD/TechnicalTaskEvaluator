# NTZ_Agentic_IITU
TechnicalTaskEvaluator — это AI-система для автоматического анализа технических заданий (ТЗ), их скоринга и последующего интерактивного диалога с пользователем.

Проект:

анализирует текст ТЗ через LLM (Gemini)
выставляет структурированные оценки по критериям
сохраняет результаты в Supabase и Google Sheets
запускает чат-агента, который помогает улучшать ТЗ
🚀 Основные возможности
📄 Загрузка и обработка технического задания (DOCX / текст)
🤖 AI-скоринг документа (Gemini API)
📊 Оценка по критериям:
стратегическая релевантность
цели и задачи
научная новизна
практическая применимость
результаты и эффект
реализуемость
💬 Чат-ассистент по конкретному ТЗ
🗃️ Хранение истории в Supabase
📈 Экспорт результатов в Google Sheets
🏗️ Архитектура проекта
📦 Общая структура
TechnicalTaskEvaluator/
│
├── backend/
│   ├── main.py                # точка входа FastAPI
│   │
│   ├── api/                  # HTTP маршруты
│   │   └── register_page.py  # регистрация, чат, скоринг
│   │
│   ├── agent_core/           # AI логика
│   │   ├── scoringAimodule.py
│   │   ├── chatAImodel.py
│   │   ├── promt.py
│   │   └── send_to_sheets.py
│   │
│   ├── services/             # утилиты
│   │   └── inputer_data_tz.py
│   │
│   └── test_doc/             # тестовые документы
│
├── credentials/              # Google service account
├── web/                      # frontend HTML
├── requirements.txt
└── .env
🧠 Архитектура решения
🔹 1. Этап скоринга
User → /api/score → Gemini AI → scoring_result

Что происходит:

документ конвертируется в текст
отправляется в Gemini
возвращается структурированный JSON
создаётся session_id
создаётся чат-агент
🔹 2. Чат-агент
User → /api/chat → TZChatAgent → Gemini Chat Model → Response

Функции:

учитывает результат скоринга
хранит историю в Supabase
восстанавливает состояние при перезапуске сервера
🔹 3. Хранение данных
Supabase используется для:
пользователей
истории чата
восстановления сессий
Google Sheets используется для:
записи результатов скоринга
аналитики и отчётности
⚙️ Технологии
FastAPI (backend API)
Gemini API (LLM)
Supabase (DB + auth + history)
Google Sheets API (экспорт данных)
Pydantic (валидация)
Uvicorn (server)
🔐 Переменные окружения (.env)

Создай .env файл:

GEMINI_API_KEY=your_key
GEMINI_CHAT_MODEL=gemini-2.0-flash
GEMINI_SCORING_MODEL=gemini-2.5-pro

SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your_key

GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_SHEET_ID=your_sheet_id
▶️ Запуск проекта
1. Установить зависимости
pip install -r requirements.txt
2. Запуск backend
cd TechnicalTaskEvaluator
uvicorn backend.main:app --reload
3. Открыть Swagger
http://127.0.0.1:8000/docs
📡 API endpoints
🔐 Auth
POST /api/register
POST /api/enter
📊 Scoring
POST /api/score
{
  "document_text": "...",
  "username": "user"
}
💬 Chat
POST /api/chat
{
  "session_id": "...",
  "message": "..."
}
DELETE /api/chat/{session_id}
🧾 Utilities
GET /db_check
GET /api/history/{session_id}
🧠 Логика session_id
создаётся в /api/score
передаётся на фронт
используется во всех запросах чата
при рестарте сервера восстанавливается из Supabase
🔄 Поток работы системы
1. Пользователь загружает ТЗ
        ↓
2. /api/score → Gemini → оценка + session_id
        ↓
3. пользователь получает session_id
        ↓
4. /api/chat → диалог с AI
        ↓
5. история сохраняется в Supabase
        ↓
6. /api/chat/{session_id} → очистка
📊 Выходные данные

Система возвращает:

общий балл (0–100)
детальную оценку критериев
экспертный комментарий
список недостатков
рекомендации по улучшению
🚀 Возможные улучшения
Redis вместо in-memory storage
JWT авторизация
Docker контейнеризация
очередь задач (Celery)
фронтенд на React/Vue
streaming ответов Gemini
👨‍💻 Авторская идея

Проект создан как:

интеллектуальная система анализа технических заданий с AI-экспертизой и интерактивным улучшением документа в режиме диалога.
