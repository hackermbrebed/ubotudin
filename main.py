import os
import asyncio
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait
from pyrogram.types import Message
from tqdm.asyncio import tqdm
from pyrogram import enums

# Kredensial API dari my.telegram.org
API_ID = os.environ.get("API_ID", "YOUR_API_ID")
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING", "YOUR_SESSION_STRING")

# Inisialisasi client Pyrogram
app = Client(
    name="my_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

# Inisialisasi blacklist
BLACKLIST = set()

# --- Fitur GCAST (Global Broadcast) ---

@app.on_message(filters.me & filters.command("gcast", prefixes="."))
async def gcast_handler(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.edit_text("Balas pesan untuk di-gcast!")
    
    target_message = message.reply_to_message
    
    # Ambil semua obrolan (grup, channel, private chat) yang ada
    dialogs = await client.get_dialogs()
    
    success_count = 0
    failed_count = 0
    
    await message.edit_text("Memulai gcast...")
    
    for dialog in tqdm(dialogs, desc="Broadcasting"):
        chat_id = dialog.chat.id
        
        # Lewati chat yang ada di blacklist
        if chat_id in BLACKLIST:
            continue
            
        try:
            if target_message.text:
                await client.send_message(chat_id, target_message.text, parse_mode=enums.ParseMode.MARKDOWN)
            elif target_message.photo:
                await client.send_photo(chat_id, target_message.photo.file_id, caption=target_message.caption, parse_mode=enums.ParseMode.MARKDOWN)
            # Anda bisa menambahkan jenis pesan lain (video, dokumen, dll) di sini
            
            success_count += 1
            await asyncio.sleep(0.5) # Jeda untuk menghindari flood
            
        except FloodWait as e:
            print(f"FloodWait: menunggu selama {e.value} detik...")
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"Gagal mengirim ke {chat_id}: {e}")
            failed_count += 1
            
    await message.edit_text(f"✅ Gcast selesai!\n\n**Berhasil**: {success_count}\n**Gagal**: {failed_count}")

# --- Fitur ADD BL (Add to Blacklist) ---

@app.on_message(filters.me & filters.command("addbl", prefixes="."))
async def addbl_handler(client: Client, message: Message):
    if not message.reply_to_message:
        chat_id = message.chat.id
    else:
        chat_id = message.reply_to_message.chat.id
        
    if chat_id in BLACKLIST:
        return await message.edit_text("Chat ini sudah ada di blacklist.")
        
    BLACKLIST.add(chat_id)
    await message.edit_text("✅ Chat berhasil ditambahkan ke **blacklist**.")

# --- Fitur Font Keren ---

# Font Map
FONT_MAP = {
    "bold": ("**", "**"),
    "italic": ("__", "__"),
    "mono": ("`", "`"),
    "strike": ("~", "~"),
    "underline": ("<u>", "</u>"),
}

@app.on_message(filters.me & filters.command(["bold", "italic", "mono", "strike", "underline"], prefixes="."))
async def font_handler(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.edit_text("Balas pesan yang ingin diformat!")
        
    text_to_format = message.reply_to_message.text
    if not text_to_format:
        return await message.edit_text("Pesan tidak memiliki teks.")
        
    font_type = message.command[0]
    
    # Ambil tag format dari FONT_MAP
    if font_type in FONT_MAP:
        start_tag, end_tag = FONT_MAP[font_type]
        formatted_text = f"{start_tag}{text_to_format}{end_tag}"
        
        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.reply_to_message.id,
            text=formatted_text,
            parse_mode=ParseMode.MARKDOWN
        )
        await message.delete()
    else:
        await message.edit_text("Jenis font tidak valid. Gunakan: .bold, .italic, .mono, .strike, .underline")

# --- Jalankan Userbot ---

print("Userbot sedang berjalan...")
app.run()
