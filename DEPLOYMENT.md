# 🚀 Инструкция по развертыванию CMS

## Локальное развертывание

### Требования
- Python 3.12+
- Node.js 18+
- Git

### Шаги установки

#### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd business-card-website
```

#### 2. Создание виртуального окружения
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 3. Установка зависимостей Python
```bash
# Используйте замороженные версии для стабильности
pip install -r requirements-frozen.txt

# Или последние совместимые версии
pip install -r requirements.txt
```

#### 4. Установка зависимостей Node.js
```bash
npm install
```

#### 5. Настройка окружения
```bash
# Скопируйте пример конфигурации
copy env.example .env  # Windows
cp env.example .env    # Linux/Mac

# Отредактируйте .env файл
notepad .env  # Windows
nano .env     # Linux/Mac
```

**Обязательно измените:**
- `JWT_SECRET` - установите уникальный секретный ключ
- `ENVIRONMENT` - `production` для продакшена
- `SECURE_COOKIES` - `true` для продакшена
- `BASE_URL` - укажите ваш домен

#### 6. Создание необходимых директорий
```bash
mkdir data uploads uploads\originals uploads\optimized cache cache\renders logs
```

#### 7. Сборка CSS
```bash
npm run build:css
```

#### 8. Инициализация базы данных
База данных создастся автоматически при первом запуске.

#### 9. Создание первого администратора
Зарегистрируйтесь через форму `/register` при первом запуске.
Первый зарегистрированный пользователь автоматически получает роль admin.

#### 10. Запуск приложения

**Для разработки:**
```bash
npm run dev
# Или
.\dev.ps1  # Windows
```

**Для production:**
```bash
npm run run
# Или
.\run.ps1  # Windows
```

## Production развертывание

### Рекомендации для production

#### 1. Использование production сервера

**Gunicorn (Linux):**
```bash
pip install gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Uvicorn с несколькими воркерами:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 2. Настройка обратного прокси (Nginx)

**Пример конфигурации Nginx:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Перенаправление на HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Статические файлы
    location /static/ {
        alias /path/to/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /uploads/ {
        alias /path/to/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Проксирование к FastAPI
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 3. Systemd сервис (Linux)

**Создайте файл `/etc/systemd/system/cms.service`:**
```ini
[Unit]
Description=Business Card CMS
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/business-card-website
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

**Активация сервиса:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable cms
sudo systemctl start cms
sudo systemctl status cms
```

#### 4. Автоматический запуск CSS сборки

**Добавьте в crontab:**
```bash
@reboot cd /path/to/business-card-website && npm run build:css
```

#### 5. Мониторинг и логирование

**Просмотр логов systemd:**
```bash
sudo journalctl -u cms -f
```

**Логи приложения:**
```bash
tail -f logs/app.log
```

#### 6. Резервное копирование

**Создайте скрипт backup.sh:**
```bash
#!/bin/bash
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Резервное копирование БД
cp data/app.db $BACKUP_DIR/app_$DATE.db

# Резервное копирование загруженных файлов
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz uploads/

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "app_*.db" -mtime +30 -delete
find $BACKUP_DIR -name "uploads_*.tar.gz" -mtime +30 -delete
```

**Добавьте в crontab (ежедневно в 2:00):**
```bash
0 2 * * * /path/to/backup.sh
```

## Обновление приложения

### 1. Остановите приложение
```bash
sudo systemctl stop cms  # Linux
# Или нажмите Ctrl+C в консоли разработки
```

### 2. Обновите код
```bash
git pull origin main
```

### 3. Обновите зависимости
```bash
# Активируйте виртуальное окружение
source venv/bin/activate  # Linux
venv\Scripts\activate     # Windows

# Обновите зависимости
pip install -r requirements-frozen.txt
npm install
```

### 4. Пересоберите CSS
```bash
npm run build:css
```

### 5. Запустите приложение
```bash
sudo systemctl start cms  # Linux
# Или npm run run
```

## Проверка развертывания

### Чек-лист после развертывания

- [ ] Приложение доступно по URL
- [ ] Статические файлы загружаются корректно
- [ ] Регистрация и вход работают
- [ ] CMS панель доступна после входа
- [ ] Загрузка изображений работает
- [ ] Редактирование текстов сохраняется
- [ ] SEO метаданные применяются
- [ ] Мультиязычность переключается
- [ ] Тёмная/светлая тема переключается
- [ ] Мобильная версия корректна

### Тестирование производительности

```bash
# Lighthouse тест
python manage_tests.py lighthouse

# Нагрузочное тестирование (опционально)
# Установите apache bench
ab -n 1000 -c 10 http://yourdomain.com/
```

## Безопасность

### Обязательные настройки безопасности

1. **Смените JWT_SECRET** на уникальное значение
2. **Включите SECURE_COOKIES** в production
3. **Используйте HTTPS** с валидным SSL сертификатом
4. **Настройте файрвол** (разрешите только 80, 443, 22)
5. **Регулярно обновляйте** зависимости
6. **Настройте резервное копирование** БД и файлов
7. **Ограничьте SSH доступ** (только ключи)
8. **Мониторьте логи** на подозрительную активность

### Hardening checklist

- [ ] Изменен JWT_SECRET
- [ ] SECURE_COOKIES=true
- [ ] HTTPS настроен
- [ ] Файрвол настроен
- [ ] SSH только по ключу
- [ ] Резервное копирование настроено
- [ ] Мониторинг логов настроен
- [ ] Fail2ban установлен (опционально)

## Решение проблем

### Приложение не запускается

1. Проверьте логи: `sudo journalctl -u cms -f`
2. Проверьте права доступа: `ls -la data/`
3. Проверьте порт: `netstat -tulpn | grep 8000`
4. Проверьте .env файл

### Статические файлы не загружаются

1. Проверьте конфигурацию Nginx
2. Проверьте права доступа: `chmod -R 755 app/static uploads`
3. Проверьте путь в конфигурации

### База данных не создается

1. Проверьте права доступа к директории `data/`
2. Убедитесь, что директория существует: `mkdir -p data`
3. Проверьте логи приложения

### Изображения не загружаются

1. Проверьте права доступа: `chmod -R 755 uploads`
2. Убедитесь, что директории созданы: `mkdir -p uploads/{originals,optimized}`
3. Проверьте размер файла (max 2MB)

## Контакты

Для поддержки и вопросов обращайтесь к администратору проекта.

---

**Версия:** 1.0.0  
**Дата:** Октябрь 2025  
**Лицензия:** MIT

