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
4. Переводим, а потом собираем переводы\
`pybabel compile -d tgbot/locales -D kai_bot`

### Обновляем переводы
1. Вытаскиваем тексты из файлов\
`pybabel extract . -o tgbot/locales/kai_bot.pot`
2. Добавляем текст в переведенные версии\
`pybabel update -d tgbot/locales -D kai_bot -i tgbot/locales/kai_bot.pot`
3. Вручную делаем переводы, а потом Собираем\
`pybabel compile -d tgbot/locales -D kai_bot`

---