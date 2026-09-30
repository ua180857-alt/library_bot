import os
import json
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from database.db import SessionLocal, Book, Category
from keyboards.admin import (
    admin_menu, cancel, add_type, add_category, edit_books, delete_books,
    edit_fields, edit_type, edit_category, confirm_delete
)

router = Router()
log = logging.getLogger(__name__)
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))


def is_admin(user_id: int) -> bool:
    return ADMIN_ID != 0 and user_id == ADMIN_ID


class AddBook(StatesGroup):
    title = State()
    author = State()
    description = State()
    language = State()
    cover = State()
    book_type = State()
    category = State()
    pdf = State()
    audio = State()


class EditBook(StatesGroup):
    value = State()
    audio = State()


async def get_categories():
    async with SessionLocal() as s:
        return (await s.execute(select(Category).order_by(Category.id))).scalars().all()


async def get_book(book_id):
    async with SessionLocal() as s:
        return await s.get(Book, book_id)


async def show_edit_book(message, book_id):
    b = await get_book(book_id)
    if not b:
        await message.answer("❌ Kitob topilmadi.", reply_markup=admin_menu())
        return
    text = (
        f"✏️ <b>Kitobni tahrirlash</b>\n\n"
        f"🆔 ID: {b.id}\n"
        f"📚 Nom: {b.title}\n"
        f"👤 Muallif: {b.author}\n"
        f"🌐 Til: {b.language or '-'}\n"
        f"📦 Turi: {b.type}\n"
        f"📄 PDF: {'Bor' if b.pdf_file_id else 'Yo‘q'}\n"
        f"🎧 Audio: {'Bor' if b.audio_file_id and b.audio_file_id != '[]' else 'Yo‘q'}\n\n"
        "O'zgartirmoqchi bo'lgan maydonni tanlang:"
    )
    await message.answer(text, reply_markup=edit_fields(book_id))


@router.message(Command("admin"))
async def admin_cmd(message: Message):
    if is_admin(message.from_user.id):
        await message.answer("🛠 <b>Admin panel</b>", reply_markup=admin_menu())


@router.callback_query(F.data == "admin:home")
async def admin_home(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id): return
    await state.clear()
    await call.message.edit_text("🛠 <b>Admin panel</b>", reply_markup=admin_menu())
    await call.answer()


@router.callback_query(F.data == "admin:cancel")
async def admin_cancel(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id): return
    await state.clear()
    await call.message.edit_text("🛠 <b>Admin panel</b>", reply_markup=admin_menu())
    await call.answer("Bekor qilindi")


@router.message(Command("add_book"))
async def add_command(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await start_add(message, state)


@router.callback_query(F.data == "admin:add")
async def add_button(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id): return
    await start_add(call.message, state)
    await call.answer()


async def start_add(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AddBook.title)
    await message.answer("➕ <b>Yangi kitob</b>\n\n1/9 📚 Kitob nomini yuboring:", reply_markup=cancel())


@router.message(AddBook.title)
async def add_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddBook.author)
    await message.answer("2/9 👤 Muallif:", reply_markup=cancel())


@router.message(AddBook.author)
async def add_author(message: Message, state: FSMContext):
    await state.update_data(author=message.text.strip())
    await state.set_state(AddBook.description)
    await message.answer("3/9 📝 Tavsif:", reply_markup=cancel())


@router.message(AddBook.description)
async def add_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(AddBook.language)
    await message.answer("4/9 🌐 Til:", reply_markup=cancel())


@router.message(AddBook.language)
async def add_language(message: Message, state: FSMContext):
    await state.update_data(language=message.text.strip())
    await state.set_state(AddBook.cover)
    await message.answer("5/9 🖼 Muqova rasmini yuboring yoki /skip bosing:", reply_markup=cancel())


@router.message(AddBook.cover)
async def add_cover(message: Message, state: FSMContext):
    if message.text == "/skip":
        cover = None
    elif message.photo:
        cover = message.photo[-1].file_id
    else:
        await message.answer("Rasm yuboring yoki /skip bosing.")
        return
    await state.update_data(cover=cover)
    await state.set_state(AddBook.book_type)
    await message.answer("6/9 📦 Kitob turini tanlang:", reply_markup=add_type())


@router.callback_query(F.data.startswith("admin:add_type:"))
async def add_type_button(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id): return
    typ = call.data.split(":")[-1]
    await state.update_data(book_type=typ)
    await state.set_state(AddBook.category)
    await call.message.edit_text("7/9 📂 Yo'nalishni tanlang:", reply_markup=add_category(await get_categories()))
    await call.answer()


@router.message(AddBook.book_type)
async def add_type_legacy(message: Message):
    await message.answer("Iltimos, kitob turini tugma orqali tanlang.")


@router.callback_query(F.data.startswith("admin:add_cat:"))
async def add_category_button(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id): return
    cid = int(call.data.split(":")[-1])
    await state.update_data(category_id=cid)
    data = await state.get_data()
    if data["book_type"] in ("read", "both"):
        await state.set_state(AddBook.pdf)
        await call.message.edit_text("8/9 📄 PDF faylini yuboring yoki /skip bosing:", reply_markup=cancel())
    else:
        await state.update_data(pdf=None, audio_parts=[])
        await state.set_state(AddBook.audio)
        await call.message.edit_text("9/9 🎧 Audio fayllarni yuboring. Tugagach /done bosing:", reply_markup=cancel())
    await call.answer()


@router.message(AddBook.category)
async def add_category_legacy(message: Message):
    await message.answer("Iltimos, yo'nalishni tugma orqali tanlang.")


@router.message(AddBook.pdf)
async def add_pdf(message: Message, state: FSMContext):
    if message.text == "/skip":
        pdf = None
    elif message.document and message.document.mime_type == "application/pdf":
        pdf = message.document.file_id
    else:
        await message.answer("PDF fayl yuboring yoki /skip bosing.")
        return
    await state.update_data(pdf=pdf, audio_parts=[])
    await state.set_state(AddBook.audio)
    await message.answer("9/9 🎧 Audio fayllarni yuboring. Tugagach /done bosing:", reply_markup=cancel())


@router.message(AddBook.audio)
async def add_audio(message: Message, state: FSMContext):
    if message.text == "/done":
        data = await state.get_data()
        async with SessionLocal() as s:
            s.add(Book(
                title=data["title"], author=data["author"], description=data["description"],
                language=data["language"], cover=data.get("cover"), pdf_file_id=data.get("pdf"),
                audio_file_id=json.dumps(data.get("audio_parts", []), ensure_ascii=False),
                type=data["book_type"], category_id=data["category_id"]
            ))
            await s.commit()
        await state.clear()
        await message.answer("✅ Kitob muvaffaqiyatli qo'shildi.", reply_markup=admin_menu())
        return
    if not message.audio:
        await message.answer("Audio fayl yuboring yoki /done bosing.")
        return
    data = await state.get_data()
    parts = data.get("audio_parts", [])
    parts.append(message.audio.file_id)
    await state.update_data(audio_parts=parts)
    await message.answer(f"✅ {len(parts)}-qism qabul qilindi. Yana yuboring yoki /done bosing.")


@router.callback_query(F.data == "admin:edit_list")
async def edit_list(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    async with SessionLocal() as s:
        books = (await s.execute(select(Book).order_by(Book.id.desc()).limit(100))).scalars().all()
    if not books:
        await call.message.edit_text("📚 Kitoblar yo'q.", reply_markup=admin_menu())
    else:
        await call.message.edit_text("✏️ Tahrirlanadigan kitobni tanlang:", reply_markup=edit_books(books))
    await call.answer()


@router.callback_query(F.data.startswith("admin:choose_edit:"))
async def choose_edit(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    await show_edit_book(call.message, int(call.data.split(":")[-1]))
    await call.answer()


@router.callback_query(F.data.startswith("admin:edit_field:"))
async def edit_field(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id): return
    _, _, _, bid, field = call.data.split(":")
    bid = int(bid)
    if field == "type":
        await call.message.edit_text("📦 Yangi turini tanlang:", reply_markup=edit_type(bid))
        await call.answer(); return
    if field == "category":
        await call.message.edit_text("📂 Yangi yo'nalishni tanlang:", reply_markup=edit_category(bid, await get_categories()))
        await call.answer(); return
    if field == "audio":
        await state.clear()
        await state.set_state(EditBook.audio)
        await state.update_data(book_id=bid, audio_parts=[])
        await call.message.answer("🎧 Yangi audio qismlarini yuboring. Tugagach /done bosing.")
        await call.answer(); return
    await state.clear()
    await state.set_state(EditBook.value)
    await state.update_data(book_id=bid, field=field)
    prompts = {
        "title": "📚 Yangi kitob nomi:", "author": "👤 Yangi muallif:",
        "description": "📝 Yangi tavsif:", "language": "🌐 Yangi til:",
        "cover": "🖼 Yangi muqova rasmini yuboring yoki /skip:",
        "pdf": "📄 Yangi PDF yuboring yoki /skip:"
    }
    await call.message.answer(prompts[field])
    await call.answer()


@router.message(EditBook.value)
async def edit_value(message: Message, state: FSMContext):
    data = await state.get_data(); bid = data["book_id"]; field = data["field"]
    value = None
    if field == "cover":
        if message.text == "/skip": value = None
        elif message.photo: value = message.photo[-1].file_id
        else: return await message.answer("Rasm yuboring yoki /skip bosing.")
    elif field == "pdf":
        if message.text == "/skip": value = None
        elif message.document and message.document.mime_type == "application/pdf": value = message.document.file_id
        else: return await message.answer("PDF yuboring yoki /skip bosing.")
    else:
        value = (message.text or "").strip()
        if not value: return await message.answer("Qiymat bo'sh bo'lmasin.")
    async with SessionLocal() as s:
        b = await s.get(Book, bid)
        if not b: await state.clear(); return await message.answer("❌ Kitob topilmadi.", reply_markup=admin_menu())
        setattr(b, field, value)
        await s.commit()
    await state.clear()
    await message.answer("✅ O'zgartirish saqlandi.", reply_markup=admin_menu())
    await show_edit_book(message, bid)


@router.callback_query(F.data.startswith("admin:set_type:"))
async def set_type(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    _, _, _, bid, typ = call.data.split(":")
    async with SessionLocal() as s:
        b = await s.get(Book, int(bid))
        if b: b.type = typ; await s.commit()
    await call.message.edit_text("✅ Kitob turi o'zgartirildi.")
    await show_edit_book(call.message, int(bid)); await call.answer()


@router.callback_query(F.data.startswith("admin:set_cat:"))
async def set_cat(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    _, _, _, bid, cid = call.data.split(":")
    async with SessionLocal() as s:
        b = await s.get(Book, int(bid))
        if b: b.category_id = int(cid); await s.commit()
    await call.message.edit_text("✅ Yo'nalish o'zgartirildi.")
    await show_edit_book(call.message, int(bid)); await call.answer()


@router.message(EditBook.audio)
async def edit_audio(message: Message, state: FSMContext):
    data = await state.get_data(); bid = data["book_id"]
    if message.text == "/done":
        async with SessionLocal() as s:
            b = await s.get(Book, bid)
            if b: b.audio_file_id = json.dumps(data.get("audio_parts", []), ensure_ascii=False); await s.commit()
        await state.clear(); await message.answer("✅ Audio yangilandi.", reply_markup=admin_menu()); await show_edit_book(message, bid); return
    if not message.audio: return await message.answer("Audio yuboring yoki /done bosing.")
    parts = data.get("audio_parts", []); parts.append(message.audio.file_id)
    await state.update_data(audio_parts=parts)
    await message.answer(f"✅ {len(parts)}-qism qabul qilindi. Yana yuboring yoki /done bosing.")


@router.callback_query(F.data == "admin:delete_list")
async def delete_list(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    async with SessionLocal() as s:
        books = (await s.execute(select(Book).order_by(Book.id.desc()).limit(100))).scalars().all()
    if not books:
        await call.message.edit_text("📚 Kitoblar yo'q.", reply_markup=admin_menu())
    else:
        await call.message.edit_text("🗑 O'chiriladigan kitobni tanlang:", reply_markup=delete_books(books))
    await call.answer()


@router.callback_query(F.data.startswith("admin:delete_confirm:"))
async def delete_confirm(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    bid = int(call.data.split(":")[-1])
    b = await get_book(bid)
    if not b: return await call.answer("Kitob topilmadi.", show_alert=True)
    await call.message.edit_text(f"⚠️ <b>{b.title}</b> ni o'chirmoqchimisiz?", reply_markup=confirm_delete(bid))
    await call.answer()


@router.callback_query(F.data.startswith("admin:delete:"))
async def delete_book(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    bid = int(call.data.split(":")[-1])
    async with SessionLocal() as s:
        b = await s.get(Book, bid)
        if b:
            await s.delete(b); await s.commit()
    await call.message.edit_text("🗑 Kitob o'chirildi.", reply_markup=admin_menu())
    await call.answer()


@router.callback_query(F.data == "admin:list")
async def admin_list(call: CallbackQuery):
    if not is_admin(call.from_user.id): return
    async with SessionLocal() as s:
        books = (await s.execute(select(Book).order_by(Book.id.desc()).limit(100))).scalars().all()
    if not books:
        await call.message.edit_text("📚 Kitoblar yo'q.", reply_markup=admin_menu())
        return await call.answer()
    for b in books:
        await call.message.answer(f"#{b.id} <b>{b.title}</b>\n👤 {b.author}\n📦 {b.type}")
    await call.answer()
