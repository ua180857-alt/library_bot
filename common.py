from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

def main_menu():
    b = InlineKeyboardBuilder()
    for text, data in [
        ("📚 O'qish uchun kitoblar", "section:read"),
        ("🎧 Audio kitoblar", "section:audio"),
        ("🔍 Qidirish", "search"),
        ("⭐ Sevimlilar", "favorites"),
        ("ℹ️ Bot haqida", "about"),
    ]:
        b.button(text=text, callback_data=data)
    b.adjust(1)
    return b.as_markup()

def bottom():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="back"),
          InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="home"))
    return b.as_markup()

def categories(section):
    names = [
        "Badiiy adabiyot", "Diniy va ma'naviy", "Tarix",
        "Psixologiya va shaxsiy rivojlanish", "Biznes va moliya",
        "Ilm-fan va texnologiya", "Bolalar adabiyoti",
        "Darsliklar va o'quv qo'llanmalar",
    ]
    b = InlineKeyboardBuilder()
    for i, name in enumerate(names, 1):
        b.button(text=name, callback_data=f"cat:{section}:{i}")
    b.adjust(1)
    b.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="back"),
          InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="home"))
    return b.as_markup()

def books_keyboard(books, section):
    b = InlineKeyboardBuilder()
    icon = "📖" if section == "read" else "🎧"
    for x in books:
        b.button(text=f"{icon} {x.title[:45]}", callback_data=f"book:{x.id}")
    b.adjust(1)
    return b

def book_card(book_id, favorite, pdf, audio):
    b = InlineKeyboardBuilder()
    if pdf: b.button(text="📄 PDF yuklab olish", callback_data=f"pdf:{book_id}")
    if audio: b.button(text="🎧 Audio tinglash", callback_data=f"audio:{book_id}:0")
    b.button(text="⭐ Sevimlilardan olib tashlash" if favorite else "⭐ Sevimlilarga qo'shish",
             callback_data=f"fav:{book_id}")
    b.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="back"),
          InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="home"))
    b.adjust(1)
    return b.as_markup()

def pager(section, category_id, page, pages):
    b = InlineKeyboardBuilder()
    if page > 1: b.button(text="⬅️", callback_data=f"page:{section}:{category_id}:{page-1}")
    b.button(text=f"{page}/{pages}", callback_data="noop")
    if page < pages: b.button(text="➡️", callback_data=f"page:{section}:{category_id}:{page+1}")
    b.adjust(3)
    b.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"categories:{section}"),
          InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="home"))
    return b.as_markup()

def audio_nav(book_id, index, total):
    b = InlineKeyboardBuilder()
    if index > 0: b.button(text="◀️ Oldingi qism", callback_data=f"audio:{book_id}:{index-1}")
    if index + 1 < total: b.button(text="▶️ Keyingi qism", callback_data=f"audio:{book_id}:{index+1}")
    b.adjust(2)
    b.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="back"),
          InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="home"))
    return b.as_markup()

def admin_menu():
    b = InlineKeyboardBuilder()
    b.button(text="➕ Kitob qo'shish", callback_data="admin:add")
    b.button(text="📚 Kitoblar", callback_data="admin:list")
    b.button(text="🏠 Bosh menyu", callback_data="home")
    b.adjust(1)
    return b.as_markup()

def admin_book(book_id):
    b = InlineKeyboardBuilder()
    b.button(text="✏️ Tahrirlash", callback_data=f"admin:edit:{book_id}")
    b.button(text="🗑 O'chirish", callback_data=f"admin:delete:{book_id}")
    b.adjust(2)
    return b.as_markup()
