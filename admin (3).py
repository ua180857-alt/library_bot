from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton


def admin_menu():
    b = InlineKeyboardBuilder()
    b.button(text="➕ Kitob qo'shish", callback_data="admin:add")
    b.button(text="✏️ Kitobni tahrirlash", callback_data="admin:edit_list")
    b.button(text="🗑 Kitobni o'chirish", callback_data="admin:delete_list")
    b.button(text="📚 Barcha kitoblar", callback_data="admin:list")
    b.button(text="🏠 Bosh menyu", callback_data="home")
    b.adjust(1)
    return b.as_markup()


def cancel():
    b = InlineKeyboardBuilder()
    b.button(text="❌ Bekor qilish", callback_data="admin:cancel")
    return b.as_markup()


def add_type():
    b = InlineKeyboardBuilder()
    b.button(text="📖 Faqat PDF", callback_data="admin:add_type:read")
    b.button(text="🎧 Faqat audio", callback_data="admin:add_type:audio")
    b.button(text="📚 PDF + audio", callback_data="admin:add_type:both")
    b.button(text="❌ Bekor qilish", callback_data="admin:cancel")
    b.adjust(1)
    return b.as_markup()


def add_category(categories):
    b = InlineKeyboardBuilder()
    for c in categories:
        b.button(text=c.name, callback_data=f"admin:add_cat:{c.id}")
    b.button(text="❌ Bekor qilish", callback_data="admin:cancel")
    b.adjust(1)
    return b.as_markup()


def edit_books(books):
    b = InlineKeyboardBuilder()
    for book in books:
        b.button(text=f"#{book.id} — {book.title[:35]}", callback_data=f"admin:choose_edit:{book.id}")
    b.button(text="🔙 Admin panel", callback_data="admin:home")
    b.adjust(1)
    return b.as_markup()


def delete_books(books):
    b = InlineKeyboardBuilder()
    for book in books:
        b.button(text=f"🗑 #{book.id} — {book.title[:35]}", callback_data=f"admin:delete_confirm:{book.id}")
    b.button(text="🔙 Admin panel", callback_data="admin:home")
    b.adjust(1)
    return b.as_markup()


def edit_fields(book_id):
    b = InlineKeyboardBuilder()
    fields = [
        ("📚 Nom", "title"),
        ("👤 Muallif", "author"),
        ("📝 Tavsif", "description"),
        ("🌐 Til", "language"),
        ("🖼 Muqova", "cover"),
        ("📦 Turi", "type"),
        ("📂 Yo'nalish", "category"),
        ("📄 PDF", "pdf"),
        ("🎧 Audio", "audio"),
    ]
    for text, field in fields:
        b.button(text=text, callback_data=f"admin:edit_field:{book_id}:{field}")
    b.button(text="⬅️ Kitoblar", callback_data="admin:edit_list")
    b.button(text="🏠 Admin panel", callback_data="admin:home")
    b.adjust(2)
    return b.as_markup()


def edit_type(book_id):
    b = InlineKeyboardBuilder()
    for label, value in [("📖 PDF", "read"), ("🎧 Audio", "audio"), ("📚 Ikkalasi", "both")]:
        b.button(text=label, callback_data=f"admin:set_type:{book_id}:{value}")
    b.button(text="🔙 Orqaga", callback_data=f"admin:choose_edit:{book_id}")
    b.adjust(1)
    return b.as_markup()


def edit_category(book_id, categories):
    b = InlineKeyboardBuilder()
    for c in categories:
        b.button(text=c.name, callback_data=f"admin:set_cat:{book_id}:{c.id}")
    b.button(text="🔙 Orqaga", callback_data=f"admin:choose_edit:{book_id}")
    b.adjust(1)
    return b.as_markup()


def confirm_delete(book_id):
    b = InlineKeyboardBuilder()
    b.button(text="✅ Ha, o'chirish", callback_data=f"admin:delete:{book_id}")
    b.button(text="❌ Yo'q", callback_data="admin:delete_list")
    b.adjust(1)
    return b.as_markup()
