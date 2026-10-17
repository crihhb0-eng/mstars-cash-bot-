import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    LabeledPrice,
    PreCheckoutQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

# ضع توكن البوت الخاص بك هنا بين القوسين
TOKEN = "YOUR_BOT_TOKEN_HERE"

logging.basicConfig(level=logging.INFO)
router = Router()

# حالات المحادثة لجمع عنوان المحفظة
class WalletState(StatesGroup):
    waiting_for_wallet = State()

@router.message(Command("start"))
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ شراء Stars مقابل USDT", callback_data="buy_stars")],
        [InlineKeyboardButton(text="💳 سحب أرباح TRC20", callback_data="withdraw_usdt")]
    ])
    await message.answer(
        "مرحباً بك في بوت MStars Cash لتبادل وتداول Telegram Stars و USDT.\nاختر ما يناسبك:",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "buy_stars")
async def process_buy_stars(callback: callback_query):
    await callback.message.answer_invoice(
        title="شراء نجوم تليجرام",
        description="شحن رصيد 100 Telegram Stars",
        payload="stars_100_payload",
        currency="XTR",
        prices=[LabeledPrice(label="Stars", amount=100)]
    )
    await callback.answer()

@router.callback_query(F.data == "withdraw_usdt")
async def process_withdraw(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("الرجاء إرسال عنوان محفظة TRC20 (USDT) الخاصة بك:")
    await state.set_state(WalletState.waiting_for_wallet)
    await callback.answer()

@router.message(WalletState.waiting_for_wallet)
async def receive_wallet(message: Message, state: FSMContext):
    wallet_address = message.text
    if not wallet_address.startswith("T") or len(wallet_address) < 30:
        await message.answer("عذراً، عنوان محفظة TRC20 غير صالح. يرجى التأكد وإرساله مجدداً:")
        return
    
    await state.update_data(wallet=wallet_address)
    await message.answer(f"تم حفظ عنوان المحفظة بنجاح:\n`{wallet_address}`\nسيتم معالجة الطلب قريباً.", parse_mode="Markdown")
    await state.clear()

@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def successful_payment(message: Message):
    await message.answer("تم دفع Telegram Stars بنجاح! شكراً لك، سيتم تنفيذ طلبك فوراً.")

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
