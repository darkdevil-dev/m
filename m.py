import asyncio
import logging
import random
import os
import time
import smtplib
import pymongo
from email.mime.text import MIMEText
from pyrogram import Client, filters
from pyrogram.types import Message
from cryptography.fernet import Fernet
from datetime import datetime
from pyromod import listen

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGO_URI = "mongodb+srv://massmails:massmails@cluster0.ra96m.mongodb.net/"
mongo_client = pymongo.MongoClient(MONGO_URI)
db = mongo_client['aryan']
authorized_users_collection = db['authorized_users']
unauthorized_users_collection = db['unauthorized_users']

OWNER_ID = 7697910480

# Email Configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

# Encryption Key Setup
KEY_FILE = "secret.key"
PASSWORD_FILE = "password.enc"

bot = Client(
    "bot",
    api_id=29690940,
    api_hash="8a13349a897b290d2553e11f2860691c",
    bot_token="7536020028:AAGCmOyTd6zyusyUxsH98nuoLeKAdCATo2o"
)

# Authorization Check
def is_authorized(user_id):
    return authorized_users_collection.find_one({'user_id': user_id}) is not None

# Track Unauthorized Users
def track_unauthorized_user(user_id):
    if not unauthorized_users_collection.find_one({'user_id': user_id}):
        unauthorized_users_collection.insert_one({'user_id': user_id, 'timestamp': time.time()})

# 📌 Command: Send Bulk Emails
@bot.on_message(filters.command("send"))
async def send(client: Client, message: Message):
    user_id = message.from_user.id

    # Check if user is authorized
    if not is_authorized(user_id):
        track_unauthorized_user(user_id)
        await message.reply(f"Hey {message.from_user.mention}, You are not authorized to use this bot. Contact @ogcpr for access.")
        return

    # Function to get user input safely
    async def get_input(prompt):
        await message.reply(prompt)
        return (await client.listen(message.chat.id, filter=filters.user(user_id))).text

    # Step 1: Ask for sender email
    sender_email = await get_input("📧 Enter the sender email address:")

    # Step 2: Check if password is saved
    if os.path.exists(PASSWORD_FILE):
        sender_password = open(PASSWORD_FILE, "r").read().strip()
        await message.reply("🔐 Password already saved. Enter the subject:")
    else:
        sender_password = await get_input("🔐 Enter the sender email password:")
        with open(PASSWORD_FILE, "w") as file:
            file.write(sender_password)

    # Step 3: Ask for subject
    subject = await get_input("✉️ Enter the email subject:")

    # Step 4: Ask for body
    body = await get_input("📄 Enter the email body:")

    # Step 5: Ask for recipient
    recipient = await get_input("📨 Enter the recipient email address:")

    # Step 6: Ask for number of emails
    while True:
        count_text = await get_input("🔢 Enter the number of emails to send:")
        try:
            count = int(count_text)
            break
        except ValueError:
            await message.reply("❌ Invalid number. Please enter a valid number.")

    msg = await message.reply(f"⏳ Sending {count} emails...")

    # 📌 Function to Send Emails
    async def send_email():
        for i in range(count):
            try:
                email_msg = MIMEText(body)
                email_msg['Subject'] = subject + " " + str(random.randint(1, 100))
                email_msg['From'] = sender_email
                email_msg['To'] = recipient

                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, recipient, email_msg.as_string())

                await msg.edit(f"📧 Emails sent: {i + 1}/{count}")
                await asyncio.sleep(3)  # **Delay to avoid spam detection**
            except smtplib.SMTPException as e:
                logger.error(f"❌ Email sending failed: {e}")
                await msg.edit(f"❌ Error sending email: {e}")
                break

    await send_email()
    await msg.edit(f"✅ All {count} emails sent successfully!")

bot.run()
