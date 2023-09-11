# Telegram бот КАИ

---

## Локализация
***kai_bot*** - **домен для I18N из окружения (можно менять на любой другой)**
### Запускаем первый раз
1. Вытаскиваем тексты из файлов (он сам находит)\
`pybabel extract . -o tgbot/locales/kai_bot.pot`
2. Создаём папку для перевода на английский\
`pybabel init -i tgbot/locales/kai_bot.pot -d tgbot/locales -D kai_bot -l en`
3. То же, на русский\
`pybabel init -i tgbot/locales/kai_bot.pot -d tgbot/locales -D kai_bot -l ru`
4. То же, на татарский\
`pybabel init -i tgbot/locales/kai_bot.pot -d tgbot/locales -D kai_bot -l tt`
5. Переводим, а потом компилируем переводы\
`pybabel compile -d tgbot/locales -D kai_bot`

### Обновляем переводы
1. Вытаскиваем тексты из файлов\
`pybabel extract . -o tgbot/locales/kai_bot.pot`
2. Добавляем текст в переведенные версии\
`pybabel update -d tgbot/locales -D kai_bot -i tgbot/locales/kai_bot.pot`
3. Вручную делаем переводы, а потом компилируем\
`pybabel compile -d tgbot/locales -D kai_bot`

---

## Миграции

Для миграций используется alembic

### Первый запуск
1. Инициализация alembic -`alembic init -t async <path>`\
В корне проекта появится `alembic.ini`, а по указанному пути появится папка с миграциями.
В `alembic.ini` нужно в `sqlalchemy.url` вписать ссылку для подключения к БД, а в папке с миграциями в файле `env.py` 
нужно импортировать `Base` из `tgbot.services.database.base` и в `target_metadata` указать `Base.metadata`
2. Создание скрипта миграции - `alembic revision -m "<message>" --autogenerate`
3. Проведение миграций - `alembic upgrade head`

---