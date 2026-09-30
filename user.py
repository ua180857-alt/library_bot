import json, logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, func, or_

from database.db import SessionLocal, User, Category, Book, Favorite
from keyboards.common import main_menu, bottom, categories, books_keyboard, book_card, pager, audio_nav

router = Router()
log = logging.getLogger(__name__)

class Search(StatesGroup):
    query = State()

async def ensure_user(tg):
    async with SessionLocal() as s:
        u = (await s.execute(select(User).where(User.telegram_id == tg.id))).scalar_one_or_none()
        if not u:
            s.add(User(telegram_id=tg.id, username=tg.username, first_name=tg.first_name))
        else:
            u.username, u.first_name = tg.username, tg.first_name
        await s.commit()

async def show_book(message, book_id, telegram_id):
    async with SessionLocal() as s:
        b = await s.get(Book, book_id)
        if not b: return
        u = (await s.execute(select(User).where(User.telegram_id == telegram_id))).scalar_one_or_none()
        fav = bool(u and (await s.execute(select(Favorite).where(
            Favorite.user_id == u.id, Favorite.book_id == b.id))).scalar_one_or_none())
        audio = bool(b.audio_file_id) and b.type in ("audio", "both")
        pdf = bool(b.pdf_file_id) and b.type in ("read", "both")
        text = (f"📚 <b>{b.title}</b>\n👤 Muallif: {b.author}\n"
                f"🌐 Til: {b.language or 'O‘zbekcha'}\n\n"
                f"📝 {b.description or 'Tavsif mavjud emas.'}")
        kb = book_card(b.id, fav, pdf, audio)
        if b.cover:
            await message.answer_photo(b.cover, caption=text, reply_markup=kb)
        else:
            await message.answer(text, reply_markup=kb)

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await ensure_user(message.from_user)
    await message.answer("📚 <b>Kutubxona botiga xush kelibsiz!</b>\n\nBo'limni tanlang:", reply_markup=main_menu())

@router.message(Command("search"))
async def search_cmd(message: Message, state: FSMContext):
    await state.set_state(Search.query)
    await message.answer("🔍 Kitob nomi yoki muallifini yozing:", reply_markup=bottom())

@router.callback_query(F.data == "home")
async def home(c: CallbackQuery, state: FSMContext):
    await state.clear()
    await c.message.edit_text("🏠 <b>Bosh menyu</b>\n\nBo'limni tanlang:", reply_markup=main_menu())
    await c.answer()

@router.callback_query(F.data == "back")
async def back(c: CallbackQuery):
    await c.message.edit_text("🏠 <b>Bosh menyu</b>\n\nBo'limni tanlang:", reply_markup=main_menu())
    await c.answer()

@router.callback_query(F.data.startswith("section:"))
async def section(c: CallbackQuery):
    sec = c.data.split(":")[1]
    await c.message.edit_text(
        "📚 O'qish uchun yo'nalishni tanlang:" if sec == "read" else "🎧 Audio kitoblar yo'nalishini tanlang:",
        reply_markup=categories(sec))
    await c.answer()

@router.callback_query(F.data.startswith("categories:"))
async def categories_back(c: CallbackQuery):
    sec = c.data.split(":")[1]
    await c.message.edit_text("Yo'nalishni tanlang:", reply_markup=categories(sec))
    await c.answer()

@router.callback_query(F.data.startswith("cat:"))
async def category(c: CallbackQuery):
    _, sec, cid = c.data.split(":")
    await list_books(c, sec, int(cid), 1)
    await c.answer()

@router.callback_query(F.data.startswith("page:"))
async def page(c: CallbackQuery):
    _, sec, cid, p = c.data.split(":")
    await list_books(c, sec, int(cid), int(p))
    await c.answer()

async def list_books(c, sec, cid, page):
    cond = Book.type.in_(["read", "both"] if sec == "read" else ["audio", "both"])
    async with SessionLocal() as s:
        cat = await s.get(Category, cid)
        total = (await s.execute(select(func.count(Book.id)).where(Book.category_id == cid, cond))).scalar() or 0
        pages = max(1, (total + 4) // 5)
        page = max(1, min(page, pages))
        items = (await s.execute(select(Book).where(Book.category_id == cid, cond)
                  .order_by(Book.id.desc()).offset((page-1)*5).limit(5))).scalars().all()
    if not cat:
        await c.message.edit_text("❌ Yo'nalish topilmadi.", reply_markup=bottom()); return
    if not items:
        await c.message.edit_text(f"📂 <b>{cat.name}</b>\n\nKitoblar hozircha yo'q.", reply_markup=bottom()); return
    kb = books_keyboard(items, sec)
    # pager rows
    if page > 1: kb.button(text="⬅️", callback_data=f"page:{sec}:{cid}:{page-1}")
    kb.button(text=f"{page}/{pages}", callback_data="noop")
    if page < pages: kb.button(text="➡️", callback_data=f"page:{sec}:{cid}:{page+1}")
    kb.adjust(1)
    kb.row(__import__("aiogram").types.InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"categories:{sec}"),
           __import__("aiogram").types.InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="home"))
    await c.message.edit_text(f"📂 <b>{cat.name}</b>\n\nTanlang:", reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("book:"))
async def book(c: CallbackQuery):
    await show_book(c.message, int(c.data.split(":")[1]), c.from_user.id)
    await c.answer()

@router.callback_query(F.data.startswith("pdf:"))
async def pdf(c: CallbackQuery):
    async with SessionLocal() as s: b = await s.get(Book, int(c.data.split(":")[1]))
    if not b or not b.pdf_file_id: return await c.answer("PDF mavjud emas.", show_alert=True)
    await c.message.answer_document(b.pdf_file_id, caption=f"📄 {b.title}")
    await c.answer("PDF yuborildi.")

@router.callback_query(F.data.startswith("audio:"))
async def audio(c: CallbackQuery):
    _, bid, idx = c.data.split(":"); idx = int(idx)
    async with SessionLocal() as s: b = await s.get(Book, int(bid))
    if not b or not b.audio_file_id: return await c.answer("Audio mavjud emas.", show_alert=True)
    try: parts = json.loads(b.audio_file_id)
    except Exception: parts = [b.audio_file_id]
    if idx >= len(parts): return await c.answer("Qism topilmadi.", show_alert=True)
    await c.message.answer_audio(parts[idx], caption=f"🎧 {b.title}\nQism {idx+1}/{len(parts)}",
                                 reply_markup=audio_nav(b.id, idx, len(parts)))
    await c.answer()

@router.callback_query(F.data.startswith("fav:"))
async def favorite(c: CallbackQuery):
    bid = int(c.data.split(":")[1])
    async with SessionLocal() as s:
        u = (await s.execute(select(User).where(User.telegram_id == c.from_user.id))).scalar_one_or_none()
        if not u:
            u = User(telegram_id=c.from_user.id); s.add(u); await s.flush()
        f = (await s.execute(select(Favorite).where(Favorite.user_id == u.id, Favorite.book_id == bid))).scalar_one_or_none()
        if f: await s.delete(f); msg = "Sevimlilardan olib tashlandi."
        else: s.add(Favorite(user_id=u.id, book_id=bid)); msg = "Sevimlilarga qo'shildi."
        await s.commit()
    await c.answer("⭐ " + msg)
    await show_book(c.message, bid, c.from_user.id)

@router.callback_query(F.data == "favorites")
async def favorites(c: CallbackQuery):
    async with SessionLocal() as s:
        u = (await s.execute(select(User).where(User.telegram_id == c.from_user.id))).scalar_one_or_none()
        items = [] if not u else (await s.execute(select(Book).join(Favorite, Favorite.book_id == Book.id)
                   .where(Favorite.user_id == u.id).order_by(Book.id.desc()))).scalars().all()
    if not items:
        await c.message.edit_text("⭐ <b>Sevimlilar</b>\n\nHozircha bo'sh.", reply_markup=bottom())
    else:
        await c.message.edit_text("⭐ <b>Sevimli kitoblar</b>\n\nTanlang:",
                                  reply_markup=books_keyboard(items, "read").as_markup())
    await c.answer()

@router.callback_query(F.data == "about")
async def about(c: CallbackQuery):
    await c.message.edit_text(
        "ℹ️ <b>Bot haqida</b>\n\nKitoblarni yo'nalish bo'yicha topish, PDF o'qish va audio tinglash uchun kutubxona bot.",
        reply_markup=bottom())
    await c.answer()

@router.callback_query(F.data == "search")
async def search(c: CallbackQuery, state: FSMContext):
    await state.set_state(Search.query)
    await c.message.edit_text("🔍 Kitob nomi yoki muallifini yozing:", reply_markup=bottom())
    await c.answer()

@router.message(Search.query)
async def search_result(message: Message, state: FSMContext):
    q = message.text.strip()
    async with SessionLocal() as s:
        items = (await s.execute(select(Book).where(
            or_(Book.title.ilike(f"%{q}%"), Book.author.ilike(f"%{q}%"))).limit(30))).scalars().all()
    await state.clear()
    if not items:
        await message.answer("❌ Hech narsa topilmadi.", reply_markup=main_menu()); return
    await message.answer(f"🔍 <b>{len(items)} ta natija</b>\n\nTanlang:",
                         reply_markup=books_keyboard(items, "read").as_markup())

@router.callback_query(F.data == "noop")
async def noop(c: CallbackQuery):
    await c.answer()
