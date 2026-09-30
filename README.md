# Telegram Kutubxona Boti

Python + aiogram 3 + SQLAlchemy + SQLite.

## Ishga tushirish

Python 3.11+ tavsiya qilinadi.

```bash
python -m venv .venv
```

Windows:
```bash
.venv\\Scripts\\activate
```

Linux/macOS:
```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

`.env.example` ni `.env` qilib, quyidagilarni yozing:

```env
BOT_TOKEN=BOTFATHER_TOKEN
ADMIN_ID=123456789
```

So'ng:

```bash
python main.py
```

`library.db` avtomatik yaratiladi.

## Admin

- `/admin` — admin panel
- `/add_book` — FSM orqali kitob qo'shish
- `/edit_book ID` — kitob tahrirlash
- Admin paneldagi Kitoblar → O'chirish

Kitob turi:
- `read` — PDF
- `audio` — audio
- `both` — PDF + audio

Audio bir nechta qism bo'lishi mumkin: audio fayllarni ketma-ket yuboring va oxirida `/done` bosing.

PDF/audio serverga yuklanmaydi; Telegram `file_id` bazada saqlanadi.

Faqat tarqatish huquqiga ega yoki public-domain/litsenziyasi ruxsat bergan materiallardan foydalaning.
