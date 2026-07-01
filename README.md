# Dota 2 Update Tracker Bot

Отслеживает `steam_api/_HISTORY_by_date.txt` в репозитории
[muk-as/DOTA2_WEB](https://github.com/muk-as/DOTA2_WEB) и присылает новые
строки (изменения версий сборок) в Telegram-канал через GitHub Actions —
без сервера, без постоянно работающего процесса.

## Как это работает

1. GitHub Actions по расписанию (раз в 5 минут — это минимальный интервал,
   который поддерживает `schedule` в Actions) запускает `check_updates.py`.
2. Скрипт скачивает актуальный `_HISTORY_by_date.txt` из репозитория
   muk-as/DOTA2_WEB и сравнивает количество строк с тем, что было в прошлый раз
   (хранится в `state.json` в этом же репозитории).
3. Новые строки отправляются в Telegram-канал в исходном виде + подпись:

   ```
   373310 - Dota 2 Server | [v] 6836 => 6837 | 2026-06-27 00:11:04 (UTC+3)
   💙 Я люблю тебя Блю
   ```

4. Workflow коммитит обновлённый `state.json` обратно в репозиторий, чтобы
   при следующем запуске знать, что уже отправлено.

## Настройка (10 минут)

### 1. Создайте Telegram-бота
1. Напишите [@BotFather](https://t.me/BotFather) → `/newbot`.
2. Получите токен вида `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`.

### 2. Создайте канал и добавьте бота администратором
1. Создайте Telegram-канал (или используйте существующий).
2. Добавьте бота в администраторы канала (права на публикацию сообщений).
3. Узнайте ID канала:
   - Если канал публичный — можно использовать `@your_channel_username`.
   - Если приватный — перешлите любое сообщение из канала боту
     [@userinfobot](https://t.me/userinfobot) или [@getidsbot](https://t.me/getidsbot),
     он покажет ID вида `-1001234567890`.

### 3. Создайте репозиторий на GitHub
1. Создайте новый **приватный** репозиторий, например `dota2-tracker-bot`.
2. Загрузите в него файлы из этого проекта, сохранив структуру:
   ```
   .github/workflows/check.yml
   check_updates.py
   README.md
   ```

### 4. Добавьте секреты репозитория
В репозитории: **Settings → Secrets and variables → Actions → New repository secret**

| Имя секрета          | Значение                                  |
|-----------------------|--------------------------------------------|
| `TELEGRAM_BOT_TOKEN`  | токен бота от BotFather                    |
| `TELEGRAM_CHAT_ID`    | `@username` канала или числовой ID (`-100...`) |

### 5. Проверьте permissions для Actions
**Settings → Actions → General → Workflow permissions** → выберите
**"Read and write permissions"** (нужно, чтобы workflow мог коммитить `state.json`).

### 6. Запустите вручную первый раз
Вкладка **Actions → Check Dota 2 version updates → Run workflow**.
Первый запуск ничего не пришлёт в канал — он только зафиксирует текущее
состояние файла истории, чтобы не вывалить в канал всю историю разом.
Дальше все новые обновления будут приходить автоматически.

## Как получить обновления быстрее 5 минут

Стандартный `schedule` в GitHub Actions не может быть чаще, чем раз в 5 минут,
и по факту в загруженные периоды GitHub может задерживать выполнение ещё на
несколько минут — это ограничение самого GitHub, обойти его локально нельзя.

Если нужно быстрее, есть два варианта:

1. **Внешний cron-сервис** (например, [cron-job.org](https://cron-job.org) —
   бесплатный) раз в 1 минуту дёргает GitHub API и триггерит workflow через
   `repository_dispatch`:

   ```
   POST https://api.github.com/repos/<ваш_логин>/dota2-tracker-bot/dispatches
   Headers:
     Authorization: Bearer <personal access token с правом repo>
     Accept: application/vnd.github+json
   Body:
     {"event_type": "check-now"}
   ```

   Workflow уже настроен принимать этот триггер (`repository_dispatch: types: [check-now]`).

2. **Свой сервер/VPS** с постоянно работающим процессом (long polling или
   раз в 10–30 секунд) — быстрее, чем Actions, но требует отдельного хостинга.
   Если понадобится такой вариант — могу собрать и его.

## Файлы проекта

- `check_updates.py` — логика проверки и отправки в Telegram
- `.github/workflows/check.yml` — расписание и шаги CI
- `state.json` — создаётся автоматически при первом запуске, коммитится ботом
