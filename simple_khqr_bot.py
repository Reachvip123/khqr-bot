#!/usr/bin/env python
# Simple KHQR Telegram Bot (direct Cambodia VPS usage)
# Requirements: python-telegram-bot, bakong_khqr, qrcode, Pillow, python-dotenv

import os, asyncio, logging, qrcode
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters
from bakong_khqr import KHQR

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BAKONG_TOKEN = os.getenv("BAKONG_TOKEN")
BAKONG_ACCOUNT = os.getenv("BAKONG_ACCOUNT")  # numeric merchant account id
MERCHANT_NAME = os.getenv("MERCHANT_NAME")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_SECONDS", "10"))
MAX_MINUTES = int(os.getenv("MAX_WAIT_MINUTES", "6"))  # total timeout

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger("simple-khqr")

if not all([BOT_TOKEN, BAKONG_TOKEN, BAKONG_ACCOUNT, MERCHANT_NAME]):
    raise SystemExit("Missing required env vars BOT_TOKEN, BAKONG_TOKEN, BAKONG_ACCOUNT, MERCHANT_NAME")

try:
    khqr = KHQR(BAKONG_TOKEN)
except Exception as e:
    raise SystemExit(f"Failed to init KHQR: {e}")

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Send an amount (e.g. 2.50 or 10000 KHR) to generate a KHQR.")

async def handle_amount(update: Update, context: CallbackContext):
    txt = update.message.text.strip()
    parts = txt.split()
    try:
        amount = float(parts[0].replace(',', ''))
    except ValueError:
        await update.message.reply_text("Invalid amount.")
        return
    currency = "USD"
    if len(parts) > 1 and parts[1].upper() == "KHR":
        currency = "KHR"
        amount = int(amount)
    if amount <= 0:
        await update.message.reply_text("Amount must be > 0")
        return

    await update.message.reply_text(f"Generating KHQR for {amount:,} {currency} ...")
    try:
        qr_str = khqr.create_qr(
            bank_account=BAKONG_ACCOUNT,
            merchant_name=MERCHANT_NAME,
            merchant_city='Phnom Penh',
            amount=amount,
            currency=currency,
            store_label='Store',
            phone_number='012345678',
            terminal_label='Terminal01',
            bill_number=f'ORD-{update.message.chat_id}-{update.message.message_id}'
        )
        md5_hash = khqr.generate_md5(qr_str)
    except Exception as e:
        log.error(f"QR generation failed: {e}")
        await update.message.reply_text("QR generation failed. Check Bakong token/account.")
        return

    # send image
    img_path = f"qr_{md5_hash}.png"
    qrcode.make(qr_str).save(img_path)
    with open(img_path, 'rb') as f:
        await update.message.reply_photo(photo=f, caption=f"Scan & pay {amount:,} {currency}. MD5={md5_hash}")
    os.remove(img_path)

    # schedule payment checks
    context.job_queue.run_once(check_payment, when=CHECK_INTERVAL, data={
        'chat_id': update.message.chat_id,
        'md5': md5_hash,
        'amount': amount,
        'currency': currency,
        'attempt': 0
    }, name=f"pay_{md5_hash}")

async def check_payment(context: CallbackContext):
    job = context.job
    data = job.data
    attempt = data['attempt'] + 1
    data['attempt'] = attempt
    max_attempts = (MAX_MINUTES * 60) // CHECK_INTERVAL

    try:
        status = khqr.check_payment(data['md5'])  # returns status string maybe 'PAID'
        paid = status and status.upper() == 'PAID'
    except Exception as e:
        log.error(f"Payment check error: {e}")
        paid = False

    if paid:
        await context.bot.send_message(chat_id=data['chat_id'], text=f"✅ Payment received for {data['amount']:,} {data['currency']}.")
    elif attempt >= max_attempts:
        await context.bot.send_message(chat_id=data['chat_id'], text=f"Payment window expired for {data['amount']:,} {data['currency']}.")
    else:
        context.job_queue.run_once(check_payment, when=CHECK_INTERVAL, data=data, name=job.name)

async def error_handler(update, context):
    from telegram.error import Conflict
    err = context.error
    if isinstance(err, Conflict):
        log.error("Another instance is running. Shutting down.")
        await context.application.stop()
    else:
        log.error(f"Unhandled error: {err}", exc_info=True)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount))
    app.add_error_handler(error_handler)
    log.info("Bot started (simple direct KHQR mode).")
    app.run_polling()

if __name__ == '__main__':
    main()
