from pyrogram.enums import ParseMode
from telethon import TelegramClient, events
import os
import asyncio
from datetime import datetime
import random
import string
import logging

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

api_id = '29798494'
api_hash = '53273c1de3e68a9ecdb90de2dcf46f6c'

client = TelegramClient('userbot', api_id, api_hash)
device_owner_id = None
afk_reason = None

# Directory to store QR code images
QR_CODE_DIR = "qr_codes"

# Ensure the directory exists
os.makedirs(QR_CODE_DIR, exist_ok=True)

# Blacklisted group list
blacklisted_groups = []

# Watermark text
WATERMARK_TEXT = ""

# Dictionary to store failed broadcasts
failed_broadcasts = {}

# Fungsi untuk menghasilkan Task ID acak
def generate_task_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Fungsi untuk menambahkan watermark ke pesan
def append_watermark_to_message(message):
    return f"{message}\n\n{WATERMARK_TEXT}"

# Fungsi untuk memformat pesan menjadi quote block HTML
def format_as_blockquote(message):
    return f"<blockquote>{message}</blockquote>"

async def main():
    await client.start()
    logging.info("Client Created")

    global device_owner_id

    if not await client.is_user_authorized():
        phone_number = input("Please enter your phone number (with country code): ")
        try:
            await client.send_code_request(phone_number)
            logging.info("Code sent successfully!")
        except Exception as e:
            logging.error(f"Error requesting code: {e}")
            return
        
        code = input("Please enter the code you received: ")
        try:
            await client.sign_in(phone_number, code=code)
            logging.info("Signed in successfully!")
        except Exception as e:
            logging.error(f"Error during sign in: {e}")
            return

    logging.info("Client Authenticated")

    device_owner = await client.get_me()
    device_owner_id = device_owner.id
    logging.info(f"Device owner ID: {device_owner_id}")

def is_device_owner(sender_id):
    return sender_id == device_owner_id

@client.on(events.NewMessage(pattern='.gcast', outgoing=True))
async def gcast(event):
    sender = await event.get_sender()
    # Menangkap ID pesan untuk reply di akhir
    command_message_id = event.id 
    
    if not is_device_owner(sender.id):
        await client.send_message(event.chat_id, format_as_blockquote(append_watermark_to_message("❌ You are not authorized to use this command.")), parse_mode='html')
        logging.info("Unauthorized access attempt blocked.")
        return

    reply_message = await event.get_reply_message()
    if not reply_message:
        await client.send_message(event.chat_id, format_as_blockquote(append_watermark_to_message("❌ Please reply to a message, image, or video to use as the promotion content.")), parse_mode='html')
        return
    
    sent_count = 0
    failed_count = 0
    delay = 1
    task_id = generate_task_id()
    
    # Pesan status awal
    initial_message = await client.send_message(event.chat_id, format_as_blockquote(append_watermark_to_message(f"ᴘᴇʀɪɴᴛᴀʜ ꜱᴇᴅᴀɴɢ ᴅɪᴊᴀʟᴀɴᴋᴀɴ.")), parse_mode='html')
    
    groups = [dialog async for dialog in client.iter_dialogs() if dialog.is_group]
    failed_groups_list = []

    for dialog in groups:
        if dialog.id in blacklisted_groups:
            continue
        try:
            formatted_content = append_watermark_to_message(format_as_blockquote(reply_message.message))
            if reply_message.media:
                media_path = await client.download_media(reply_message.media)
                await client.send_file(dialog.id, media_path, caption=append_watermark_to_message(reply_message.message))
                os.remove(media_path)
            else:
                await client.send_message(dialog.id, formatted_content, parse_mode='html')
            sent_count += 1
            # Sunting pesan status saat ini
            await initial_message.edit(format_as_blockquote(f"ᴍᴜʟᴀɪ ᴍᴇɴʏᴇʀᴀɴɢ... ꜱᴜᴋꜱᴇꜱ: {sent_count}, ɢᴀɢᴀʟ: {failed_count}"), parse_mode='html')
            await asyncio.sleep(delay)
        except Exception as e:
            failed_count += 1
            failed_groups_list.append(f"{dialog.title} (ID: {dialog.id})")
            logging.error(f"Kegagalan di {dialog.title}: {e}")

    failed_broadcasts[task_id] = failed_groups_list

    main_result_text = (
        f"<b>⚔️ ʙᴏɴᴊᴏʟ ᴅᴏʏᴀɴ ᴛᴇᴍᴘᴇᴋ ⚔️</b>\n"
        f"𝘥𝘦𝘵𝘢𝘪𝘭:\n"
        f"<b>   ✅ ʙᴏɴᴊᴏʟ</b> : {sent_count}\n"
        f"<b>   ❌ ᴋᴜᴛ</b> : {failed_count}\n"
        f"<b>   🔥 ᴜᴅɪɴ</b> : 𝚃𝚊𝚠𝚞𝚛𝚊𝚗\n"
        f"<b>   ⚙️ ᴛᴀꜱᴋ ɪᴅ</b> : {task_id}\n"
    )

    footer_text = f"𝘗𝘰𝘸𝘦𝘳𝘦𝘥 𝘣𝘰𝘵 𝘣𝘺 𝕂𝕒𝕚𝕤𝕒𝕣 𝕌𝕕𝕚𝕟👑"

    result_blockquote = format_as_blockquote(main_result_text)

    footer_blockquote = format_as_blockquote(footer_text)

    final_message_content = f"{result_blockquote}{footer_blockquote}"
    
    await client.send_message(
        event.chat_id, 
        final_message_content, 
        parse_mode='html', 
        reply_to=command_message_id
    )
    
    await initial_message.delete()

@client.on(events.NewMessage(pattern='.bc-error', outgoing=True))
async def view_failed_broadcast(event):
    sender = await event.get_sender()
    if not is_device_owner(sender.id):
        await client.send_message(event.chat_id, format_as_blockquote(append_watermark_to_message("❌ You are not authorized to use this command.")), parse_mode='html')
        return
    
    command_parts = event.raw_text.split()
    if len(command_parts) < 2:
        await client.send_message(event.chat_id, format_as_blockquote(append_watermark_to_message("❌ Please specify a task ID. Example: .bc-error Y7705Bhe")), parse_mode='html')
        return
    
    task_id = command_parts[1]
    if task_id not in failed_broadcasts:
        await client.send_message(event.chat_id, format_as_blockquote(append_watermark_to_message("❌ Invalid or expired task ID.")), parse_mode='html')
        return
    
    failed_list = failed_broadcasts[task_id]
    if not failed_list:
        await client.send_message(event.chat_id, format_as_blockquote(append_watermark_to_message("✅ No failed groups for this broadcast!")), parse_mode='html')
        return
    
    failed_text = "❌ Failed groups for broadcast:\n"
    failed_text += "\n".join(failed_list)
    
    await client.send_message(event.chat_id, format_as_blockquote(append_watermark_to_message(failed_text)), parse_mode='html')
    
    await asyncio.sleep(3600)
    if task_id in failed_broadcasts:
        del failed_broadcasts[task_id]

@client.on(events.NewMessage(pattern='.hancurkan', outgoing=True))
async def blacklist_group(event):
    sender = await event.get_sender()
    if not is_device_owner(sender.id):
        await client.send_message(event.chat_id, format_as_blockquote(append_watermark_to_message("❌ You are not authorized to use this command.")), parse_mode='html')
        logging.info("Unauthorized access attempt blocked.")
        return

    group_id = event.chat_id
    if group_id not in blacklisted_groups:
        blacklisted_groups.append(group_id)
        await client.send_message(event.chat_id, format_as_blockquote(append_watermark_to_message("💣 𝐆𝐫𝐮𝐩 𝐢𝐧𝐢 𝐬𝐮𝐝𝐚𝐡 𝐝𝐢𝐡𝐚𝐧𝐜𝐮𝐫𝐤𝐚𝐧 𝐨𝐥𝐞𝐡 𝐊𝐚𝐢𝐬𝐚𝐫👑, 𝐬𝐞𝐤𝐚𝐫𝐚𝐧𝐠 𝐠𝐫𝐮𝐩 𝐢𝐧𝐢 𝐭𝐢𝐝𝐚𝐤 𝐚𝐤𝐚𝐧 𝐝𝐢𝐤𝐢𝐫𝐢𝐦 𝐠𝐢𝐤𝐞𝐬.")), parse_mode='html')
    else:
        blacklisted_groups.remove(group_id)
        await client.send_message(event.chat_id, format_as_blockquote(append_watermark_to_message("☀️ 𝐆𝐫𝐮𝐩 𝐢𝐧𝐢 𝐛𝐞𝐫𝐡𝐚𝐬𝐢𝐥 𝐝𝐢𝐛𝐚𝐧𝐠𝐮𝐧 𝐤𝐞𝐦𝐛𝐚𝐥𝐢 𝐨𝐥𝐞𝐡 𝐊𝐚𝐢𝐬𝐚𝐫👑.")), parse_mode='html')

@client.on(events.NewMessage(pattern='.addqr', outgoing=True))
async def add_qr(event):
    sender = await event.get_sender()
    if not is_device_owner(sender.id):
        await client.send_message(event.chat_id, format_as_blockquote(append_watermark_to_message("❌ You are not authorized to use this command.")), parse_mode='html')
        logging.info("Unauthorized access attempt blocked.")
        return

    reply_message = await event.get_reply_message()
    if not reply_message or not reply_message.media:
        await client.send_message(event.chat_id, format_as_blockquote(append_watermark_to_message("❌ Please reply to a QR code image to use this command.")), parse_mode='html')
        return

    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = os.path.join(QR_CODE_DIR, f"qr_{timestamp}.jpg")
        await client.download_media(reply_message.media, file_path)
        await client.send_message(event.chat_id, format_as_blockquote(append_watermark_to_message("✅ QR code added successfully!")), parse_mode='html')
        logging.info(f"QR code added with timestamp: {timestamp}")
    except Exception as e:
        await client.send_message(event.chat_id, format_as_blockquote(append_watermark_to_message("❌ Failed to add QR code.")), parse_mode='html')
        logging.error(f"Error: {e}")

@client.on(events.NewMessage(pattern='.getqr', outgoing=True))
async def get_qr(event):
    qr_files = sorted(os.listdir(QR_CODE_DIR))
    if not qr_files:
        await client.send_message(event.chat_id, format_as_blockquote(append_watermark_to_message("❌ No QR codes available.")), parse_mode='html')
        return

    try:
        for qr_file in qr_files:
            file_path = os.path.join(QR_CODE_DIR, qr_file)
            await client.send_file(event.chat_id, file_path, caption=append_watermark_to_message(f"🖼 QR Code: {qr_file}"))
            await asyncio.sleep(1)
    except Exception as e:
        await client.send_message(event.chat_id, format_as_blockquote(append_watermark_to_message("❌ Failed to send QR code.")), parse_mode='html')
        logging.error(f"Error sending QR code: {e}")

@client.on(events.NewMessage(pattern='.afk', outgoing=True))
async def afk(event):
    global afk_reason
    afk_reason = event.message.message[len('.afk '):].strip()
    if not afk_reason:
        afk_reason = "AFK"
    await client.send_message(event.chat_id, format_as_blockquote(append_watermark_to_message(f"💤 AFK mode enabled with reason: {afk_reason}")), parse_mode='html')
    logging.info(f"AFK mode enabled with reason: {afk_reason}")

@client.on(events.NewMessage(incoming=True))
async def handle_incoming(event):
    global afk_reason
    if afk_reason and event.mentioned:
        await client.send_message(event.chat_id, format_as_blockquote(append_watermark_to_message(f"🤖 I am currently AFK. Reason: {afk_reason}")), parse_mode='html')

@client.on(events.NewMessage(pattern='.back', outgoing=True))
async def back(event):
    global afk_reason
    afk_reason = None
    await client.send_message(event.chat_id, format_as_blockquote(append_watermark_to_message("👋 I am back now.")), parse_mode='html')
    logging.info("AFK mode disabled.")

@client.on(events.NewMessage(pattern='.prajurit', outgoing=True))
async def show_help(event):
    help_text = (
        "𝐁𝐞𝐫𝐢𝐤𝐮𝐭 𝐚𝐝𝐚𝐥𝐚𝐡 𝐩𝐞𝐫𝐢𝐧𝐭𝐚𝐡 𝐲𝐚𝐧𝐠 𝐛𝐢𝐬𝐚 𝐝𝐢𝐣𝐚𝐥𝐚𝐧𝐤𝐚𝐧 𝐛𝐨𝐭:\n\n"
        "🔥.𝐬𝐞𝐫𝐚𝐧𝐠 - 𝐏𝐞𝐫𝐢𝐧𝐭𝐚𝐡 𝐢𝐧𝐢 𝐮𝐧𝐭𝐮𝐤 𝐦𝐞𝐧𝐣𝐚𝐥𝐚𝐧𝐤𝐚𝐧 𝐩𝐞𝐧𝐲𝐞𝐫𝐛𝐮𝐚𝐧 𝐤𝐞 𝐠𝐫𝐮𝐩.\n"
        "⚔️.𝐡𝐚𝐧𝐜𝐮𝐫𝐤𝐚𝐧 - 𝐏𝐞𝐫𝐢𝐧𝐭𝐚𝐡 𝐢𝐧𝐢 𝐮𝐧𝐭𝐮𝐤 𝐦𝐞𝐧𝐠𝐡𝐚𝐧𝐜𝐮𝐫𝐤𝐚𝐧 𝐠𝐫𝐮𝐩 (𝐦𝐞𝐧𝐚𝐦𝐛𝐚𝐡𝐤𝐚𝐧 𝐤𝐞 𝐝𝐚𝐟𝐭𝐚𝐫 𝐛𝐥𝐨𝐤𝐢𝐫).\n"
        "🖼️.𝐚𝐝𝐝𝐪𝐫 - 𝐏𝐞𝐫𝐢𝐧𝐭𝐚𝐡 𝐢𝐧𝐢 𝐮𝐧𝐭𝐮𝐤 𝐦𝐞𝐧𝐲𝐢𝐦𝐩𝐚𝐧 𝐤𝐨𝐝𝐞 𝐐𝐑.\n"
        "🖼️.𝐠𝐞𝐭𝐪𝐫 - 𝐏𝐞𝐫𝐢𝐧𝐭𝐚𝐡 𝐢𝐧𝐢 𝐮𝐧𝐭𝐮𝐤 𝐦𝐞𝐧𝐝𝐚𝐩𝐚𝐭𝐤𝐚𝐧 𝐤𝐨𝐝𝐞 𝐐𝐑 𝐲𝐚𝐧𝐠 𝐝𝐢𝐬𝐢𝐦𝐩𝐚𝐧.\n"
        "🤖.𝐚𝐟𝐤 <𝐫𝐞𝐚𝐬𝐨𝐧> - 𝐏𝐞𝐫𝐢𝐧𝐭𝐚𝐡 𝐢𝐧𝐢 𝐮𝐧𝐭𝐮𝐤 𝐀𝐅𝐊.\n"
        "💣.𝐛𝐚𝐜𝐤 - 𝐏𝐞𝐫𝐢𝐧𝐭𝐚𝐡 𝐢𝐧𝐢 𝐮𝐧𝐭𝐮𝐤 𝐤𝐞𝐦𝐛𝐚𝐥𝐢 𝐝𝐚𝐫𝐢 𝐀𝐅𝐊.\n"
        "🔑.𝐛𝐜-𝐞𝐫𝐫𝐨𝐫 <𝐭𝐚𝐬𝐤_𝐢𝐝> - 𝐏𝐞𝐫𝐢𝐧𝐭𝐚𝐡 𝐢𝐧𝐢 𝐮𝐧𝐭𝐮𝐤 𝐦𝐞𝐥𝐢𝐡𝐚𝐭 𝐝𝐚𝐟𝐭𝐚𝐫 𝐠𝐫𝐮𝐩 𝐲𝐚𝐧𝐠 𝐠𝐚𝐠𝐚𝐥 𝐝𝐢𝐤𝐢𝐫𝐢𝐦𝐢 𝐩𝐞𝐬𝐚𝐧.\n"
        "🗿.𝐜𝐨𝐤 - 𝐈𝐧𝐢 𝐚𝐝𝐚𝐥𝐚𝐡 𝐮𝐦𝐩𝐚𝐭𝐚𝐧 𝐚𝐭𝐚𝐬 𝐤𝐞𝐬𝐚𝐥𝐚𝐡𝐚𝐧 𝐬𝐚𝐲𝐚, 𝐰𝐚𝐡𝐚𝐢 𝐊𝐚𝐢𝐬𝐚𝐫👑.\n\n"
        f"𝘗𝘰𝘸𝘦𝘳𝘦𝘥 𝘣𝘰𝘵 𝘣𝘺 𝕂𝕒𝕚𝕤𝕒𝕣 𝕌𝕕𝕚𝕟👑"
    )
    await client.send_message(event.chat_id, format_as_blockquote(help_text), parse_mode='html')

@client.on(events.NewMessage(pattern='.cok', outgoing=True))
async def ping(event):
    start = datetime.now()
    await client.send_message(event.chat_id, format_as_blockquote(append_watermark_to_message("🙏🏻 Maafkan prajuritmu yang lalai ini Kaisarku👑")), parse_mode='html')
    end = datetime.now()
    latency = (end - start).total_seconds() * 1000
    await client.send_message(event.chat_id, format_as_blockquote(append_watermark_to_message(f"⚔️ Total keseluruhan para pasukan yang siap bertempur: {latency:.2f} prajurit.")), parse_mode='html')

async def run_bot():
    await main()
    logging.info("Bot is running...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(run_bot())
