from telethon import TelegramClient, events
import os
import asyncio
from datetime import datetime
import random
import string

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

# Function to generate a random Task ID
def generate_task_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Function to append watermark to a message
def append_watermark_to_message(message):
    return f"{message}\n\n{WATERMARK_TEXT}"

async def main():
    await client.start()
    print("Client Created")

    global device_owner_id

    if not await client.is_user_authorized():
        phone_number = input("Please enter your phone number (with country code): ")
        try:
            await client.send_code_request(phone_number)
            print("Code sent successfully!")
        except Exception as e:
            print(f"Error requesting code: {e}")
            return
        
        code = input("Please enter the code you received: ")
        try:
            await client.sign_in(phone_number, code=code)
            print("Signed in successfully!")
        except Exception as e:
            print(f"Error during sign in: {e}")
            return

    print("Client Authenticated")

    device_owner = await client.get_me()
    device_owner_id = device_owner.id
    print(f"Device owner ID: {device_owner_id}")

def is_device_owner(sender_id):
    return sender_id == device_owner_id

@client.on(events.NewMessage(pattern='.jawa', outgoing=True))
async def gcast(event):
    sender = await event.get_sender()
    if not is_device_owner(sender.id):
        await event.respond(append_watermark_to_message("❌ You are not authorized to use this command."))
        print("Unauthorized access attempt blocked.")
        return

    reply_message = await event.get_reply_message()
    if not reply_message:
        await event.respond(append_watermark_to_message("❌ Please reply to a message, image, or video to use as the promotion content."))
        return
    
    sent_count = 0
    failed_count = 0
    delay = 5
    task_id = generate_task_id()
    owner_name = (await client.get_me()).first_name
    
    initial_message = await event.respond(append_watermark_to_message("Perintah Kaisar👑 sedang dijalankan"))
    
    groups = [dialog async for dialog in client.iter_dialogs() if dialog.is_group]
    
    # Store failed groups for this task ID
    failed_groups_list = []

    for dialog in groups:
        if dialog.id in blacklisted_groups:
            continue
        try:
            if reply_message.media:
                media_path = await client.download_media(reply_message.media)
                await client.send_file(dialog.id, media_path, caption=append_watermark_to_message(reply_message.message))
                os.remove(media_path) # Clean up downloaded media
            else:
                message_with_watermark = append_watermark_to_message(reply_message.message)
                await client.send_message(dialog.id, message_with_watermark)
            sent_count += 1
            await initial_message.edit(f"Perintah Kaisar👑... Sukses: {sent_count}, Gagal: {failed_count}")
            await asyncio.sleep(delay)
        except Exception as e:
            failed_count += 1
            failed_groups_list.append(f"{dialog.title} (ID: {dialog.id})")
            print(f"Kegagalan di {dialog.title}: {e}")

    failed_broadcasts[task_id] = failed_groups_list

    # Final result message
    message_text = (
        f"🔥 Perintah Kaisar👑 telah Sukses\n"
        f"✅ Success: {sent_count}\n"
        f"❌ Failed: {failed_count}\n"
        f"\n"
        f"⚔️ Type: penyerangan\n"
        f"⚙️ Task ID: {task_id}\n"
        f"👑 Pemegang Tahta: {owner_name}👑\n"
        f"\n"
        f"Type .bc-error {task_id} to view failed in broadcast."
    )
    
    await event.respond(message_text)
    await initial_message.delete()

@client.on(events.NewMessage(pattern='.bc-error', outgoing=True))
async def view_failed_broadcast(event):
    sender = await event.get_sender()
    if not is_device_owner(sender.id):
        await event.respond(append_watermark_to_message("❌ You are not authorized to use this command."))
        return
    
    command_parts = event.raw_text.split()
    if len(command_parts) < 2:
        await event.respond(append_watermark_to_message("❌ Please specify a task ID. Example: .bc-error tp0gmx8h"))
        return
    
    task_id = command_parts[1]
    if task_id not in failed_broadcasts:
        await event.respond(append_watermark_to_message("❌ Invalid or expired task ID."))
        return
        
    failed_list = failed_broadcasts[task_id]
    if not failed_list:
        await event.respond(append_watermark_to_message("✅ No failed groups for this broadcast!"))
        return
        
    failed_text = "❌ Failed groups for broadcast:\n"
    failed_text += "\n".join(failed_list)
    
    await event.respond(append_watermark_to_message(failed_text))
    
    # Clean up old failed broadcasts after a while
    # This is a simple cleanup, for a more robust solution, use a proper database.
    # We can delete it after 1 hour, for example.
    await asyncio.sleep(3600)
    if task_id in failed_broadcasts:
        del failed_broadcasts[task_id]

@client.on(events.NewMessage(pattern='.hancurkan', outgoing=True))
async def blacklist_group(event):
    sender = await event.get_sender()
    if not is_device_owner(sender.id):
        await event.respond(append_watermark_to_message("❌ You are not authorized to use this command."))
        print("Unauthorized access attempt blocked.")
        return

    group_id = event.chat_id
    if group_id not in blacklisted_groups:
        blacklisted_groups.append(group_id)
        await event.respond(append_watermark_to_message("💣 Grup ini sudah dihancurkan Kaisar👑, sekarang grup ini tidak akan dikirim gikes."))
    else:
        blacklisted_groups.remove(group_id)
        await event.respond(append_watermark_to_message("☀️ Grup ini berhasil dibangun kembali Kaisar👑."))

@client.on(events.NewMessage(pattern='.addqr', outgoing=True))
async def add_qr(event):
    sender = await event.get_sender()
    if not is_device_owner(sender.id):
        await event.respond(append_watermark_to_message("❌ You are not authorized to use this command."))
        print("Unauthorized access attempt blocked.")
        return

    reply_message = await event.get_reply_message()
    if not reply_message or not reply_message.media:
        await event.respond(append_watermark_to_message("❌ Please reply to a QR code image to use this command."))
        return

    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = os.path.join(QR_CODE_DIR, f"qr_{timestamp}.jpg")
        await client.download_media(reply_message.media, file_path)
        await event.respond(append_watermark_to_message("✅ QR code added successfully!"))
        print(f"QR code added with timestamp: {timestamp}")
    except Exception as e:
        await event.respond(append_watermark_to_message("❌ Failed to add QR code."))
        print(f"Error: {e}")

@client.on(events.NewMessage(pattern='.getqr', outgoing=True))
async def get_qr(event):
    qr_files = sorted(os.listdir(QR_CODE_DIR))
    if not qr_files:
        await event.respond(append_watermark_to_message("❌ No QR codes available."))
        return

    try:
        for qr_file in qr_files:
            file_path = os.path.join(QR_CODE_DIR, qr_file)
            await client.send_file(event.chat_id, file_path, caption=append_watermark_to_message(f"🖼 QR Code: {qr_file}"))
            await asyncio.sleep(1) # Optional delay to avoid spamming
    except Exception as e:
        await event.respond(append_watermark_to_message("❌ Failed to send QR code."))
        print(f"Error sending QR code: {e}")

@client.on(events.NewMessage(pattern='.afk', outgoing=True))
async def afk(event):
    global afk_reason
    afk_reason = event.message.message[len('.afk '):].strip()
    if not afk_reason:
        afk_reason = "AFK"
    await event.respond(append_watermark_to_message(f"💤 AFK mode enabled with reason: {afk_reason}"))
    print(f"AFK mode enabled with reason: {afk_reason}")

@client.on(events.NewMessage(incoming=True))
async def handle_incoming(event):
    global afk_reason
    if afk_reason and event.mentioned:
        await event.reply(append_watermark_to_message(f"🤖 I am currently AFK. Reason: {afk_reason}"))

@client.on(events.NewMessage(pattern='.back', outgoing=True))
async def back(event):
    global afk_reason
    afk_reason = None
    await event.respond(append_watermark_to_message("👋 I am back now."))
    print("AFK mode disabled.")

@client.on(events.NewMessage(pattern='.prajurit', outgoing=True))
async def show_help(event):
    help_text = (
        "**Siap Kaisar Udin👑, saya siap menjalankan perintah:**\n"
        ".gcast - Perintah ini untuk menjalankan penyerbuan ke grup.\n"
        ".hancurkan - Perintah ini untuk menghancurkan grup (menambahkan ke daftar blokir).\n"
        ".addqr - Perintah ini untuk menyimpan kode QR.\n"
        ".getqr - Perintah ini untuk mendapatkan kode QR yang disimpan.\n"
        ".afk <reason> - Perintah ini untuk AFK.\n"
        ".back - Perintah ini untuk kembali dari AFK.\n"
        ".bc-error <task_id> - Perintah ini untuk melihat daftar grup yang gagal dikirimi pesan.\n"
        ".cok - Ini adalah umpatan atas kesalahan saya, wahai Kaisar👑.\n"
        f"\n{WATERMARK_TEXT}"
    )
    await event.respond(help_text)

@client.on(events.NewMessage(pattern='.cok', outgoing=True))
async def ping(event):
    start = datetime.now()
    await event.respond(append_watermark_to_message("🙏🏻 Maafkan prajuritmu yang lalai ini Kaisarku👑"))
    end = datetime.now()
    latency = (end - start).total_seconds() * 1000
    await event.respond(append_watermark_to_message(f"🌏 Total keseluruhan para pasukan yang siap bertempur: {latency:.2f} prajurit"))

async def run_bot():
    await main()
    print("Bot is running...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(run_bot())
