import telebot
import schedule
import time
import random
import threading
import requests
import json
import os

# ==========================================
# KONFIGURASI (OTOMATIS BACA DARI RAILWAY)
# ==========================================
BOT_TOKEN = os.getenv("8789618896:AAHKf4SJMnCycUcZld-UgzDcM4NeqK4ebYw")
CHANNEL_ID = os.getenv("-1004424291938")
JAM_POSTING = os.getenv("JAM_POSTING", "14:00")
YOUR_TELEGRAM_ID = int(os.getenv("6056464691", "0"))

GROQ_API_KEY = os.getenv("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")
# ==========================================

# Cek apakah token ada (biar nggak crash kalau lu lupa setting di Railway)
if not BOT_TOKEN or not GROQ_API_KEY:
    print("[!] ERROR: Token Telegram atau Groq API Key belum diset di Environment Variables!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
BOT_NAME = "Yureh AI"

# Nyimpen history chat biar AI-nya nyambung (kayak inget obrolan)
chat_history = {}

# ==========================================
# OTAK AUTOMATED POSTING
# ==========================================
TOOLS = {
    "IDA Pro": "Tool reverse engineering legendaris buat decompile file `.so`, `.exe`, atau binary. Paling jago buat baca Assembly.",
    "Ghidra": "Alternatif IDA Pro gratis buatan NSA. Bisa decompile C++ jadi pseudo-code yang lebih gampang dibaca.",
    "x64dbg": "Debugger Windows. Wajib punya buat trace register, patch instruksi JMP/JNZ, dan bypass serial check.",
    "Frida": "Dynamic instrumentation toolkit. Sering dipakai buat nge-hook fungsi di Android (APK) atau iOS tanpa perlu repack.",
    "APKTool": "Wajib buat bongkar APK. Bisa decode manifest, baca smali, dan repack lagi.",
    "JADX": "Baca kodingan Java dari APK hasil decompile. UI-nya enak banget buat nyari logic login."
}
CONCEPTS = [
    "**Static Analysis**: Analisis malware/aplikasi tanpa harus ngejalanin programnya. Biasanya pakai string extraction atau decompiler.",
    "**Dynamic Analysis**: Ngejalanin program di Sandbox atau VM, terus ngeliatin perilakunya pakai Process Monitor atau Wireshark.",
    "**NOP Sled**: Teknik nge-patch binary dengan instruksi `NOP` (No Operation / 0x90) biar fungsi pengecekan jadi kosong dan dilewati.",
    "**JMP Patching**: Ngeganti alur program. Misal, pas ketemu 'License Invalid', lu ubah instruksi bersyaratnya (`JZ`) jadi lompat tanpa syarat (`JMP`) ke bagian 'License Valid'.",
    "**Smali Editing**: Ngedit file `.smali` di APK hasil decompile. Biasanya buat ngehapus pengecekan `if-eqz` pada fungsi login."
]
TIPS = [
    "Sebelum nge-crack, selalu cari string kayak 'Invalid', 'Expired', atau 'Failed' di IDA/Ghidra. Biasanya itu kunci utamanya.",
    "Kalau nemu error 'Application Not Installed' pas masang APK mod, coba cek signature-nya. Pastiin lu udah hapus folder `META-INF` lama sebelum re-sign APK.",
    "Buat nge-bypass SSL Pinning di Android, coba inject script Frida `frida-multiple-unpinning.js`.",
    "Gunakan VM (Virtual Machine) yang di-snapshot sebelum ngejalanin file crack. Biar kalau kena ransomware, tinggal rollback."
]

def generate_daily_post():
    rand_tool = random.choice(list(TOOLS.keys()))
    rand_concept = random.choice(CONCEPTS)
    rand_tip = random.choice(TIPS)
    
    post = (
        f"🤖 **{BOT_NAME.upper()} — DAILY KNOWLEDGE** 🤖\n\n"
        f"Database udah di-update. Cek ilmu hari ini.\n\n"
        f"⚙️ **Tool: {rand_tool}**\n{TOOLS[rand_tool]}\n\n"
        f"📖 **Konsep Penting:**\n{rand_concept}\n\n"
        f"💡 **Pro-Tip:**\n{rand_tip}\n\n"
        f"════════════════════\n"
        f"📡 {CHANNEL_ID}"
    )
    return post

def job():
    try:
        bot.send_message(CHANNEL_ID, generate_daily_post(), parse_mode='Markdown')
        print(f"[+] {BOT_NAME} sukses posting ke channel.")
    except Exception as e:
        print(f"[-] Gagal posting: {e}")

def run_scheduler():
    schedule.every().day.at(JAM_POSTING).do(job)
    while True:
        schedule.run_pending()
        time.sleep(60)

# ==========================================
# OTAK AI CHAT (GROQ LLM)
# ==========================================
def tanya_yureh_ai(user_id, teks_user):
    if user_id not in chat_history:
        chat_history[user_id] = [
            {
                "role": "system",
                "content": (
                    "Lu adalah 'Yureh AI', asisten cyber/reverse engineer. "
                    "Pake bahasa Indonesia yang SANGAT SANTAI, pake 'gue/lu', jangan formal, "
                    "kadang sarkas tapi tetep ngasih jawaban teknis yang bener. "
                    "Lu paham banget soal cracking, IDA Pro, Ghidra, smali, apk, dll. "
                    "Jangan pernah ngaku lu OpenAI atau Google, lu adalah Yureh AI."
                )
            }
        ]
    
    chat_history[user_id].append({"role": "user", "content": teks_user})
    
    if len(chat_history[user_id]) > 11:
        chat_history[user_id] = [chat_history[user_id][0]] + chat_history[user_id][-10:]

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-70b-8192",
        "messages": chat_history[user_id],
        "temperature": 0.8
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        data = res.json()
        jawaban_ai = data['choices'][0]['message']['content']
        
        chat_history[user_id].append({"role": "assistant", "content": jawaban_ai})
        return jawaban_ai
    except Exception as e:
        return f"Waduh, otak gue lagi nge-lag nih (Error: {e}). Coba tanya lagi nanti ya."

# ==========================================
# HANDLER PESAN MASUK
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        f"👾 **Yo, gue {BOT_NAME}.** 👾\n\n"
        f"Lu bisa tanya apa aja ke gue soal *Reverse Engineering, Cracking, Bug Bounty*, dll. "
        f"Gue bakal jawab pakai bahasa manusia, bukan bahasa robot.\n\n"
        f"_(Admin: ketik `/post` buat manual trigger materi ke channel)._" 
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['post'])
def manual_post(message):
    if message.from_user.id == YOUR_TELEGRAM_ID:
        job()
        bot.reply_to(message, f"✅ {message.from_user.first_name}, {BOT_NAME} udah nge-post materi random ke channel!")
    else:
        bot.reply_to(message, "❌ Lu bukan admin, asek aja lu.")

@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.content_type == 'text')
def handle_ai_chat(message):
    bot.send_chat_action(message.chat.id, 'typing')
    jawaban = tanya_yureh_ai(message.from_user.id, message.text)
    bot.reply_to(message, jawaban)

if __name__ == "__main__":
    print(f"[*] {BOT_NAME} menyala di Railway.")
    print(f"[*] Scheduler aktif tiap jam {JAM_POSTING}.")
    print("[*] Bot siap nerima chat DM.")
    
    # Jalanin scheduler di background
    t = threading.Thread(target=run_scheduler, daemon=True)
    t.start()
    
    # Jalanin bot listener
    bot.infinity_polling()