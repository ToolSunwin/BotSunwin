import requests
import time
import threading
from flask import Flask
from telegram import Bot, Update
from telegram.ext import CommandHandler, Updater, CallbackContext
import json
import os

# 🔐 Đọc token từ biến môi trường
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_ID = int(os.getenv('GROUP_ID'))
ADMIN_ID = int(os.getenv('ADMIN_ID'))

API_URL = 'https://wanglinapiws.up.railway.app/api/taixiu'

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)
history = []
is_running = True

def du_doan_theo_chuoi(chain):
    # Thuật toán theo chuỗi T/X
    if chain.endswith("TTT") or chain.endswith("T T T"):
        return "XỈU", 90, "3 TÀI liên tiếp, khả năng cao đảo sang XỈU."
    elif chain.endswith("XXX") or chain.endswith("X X X"):
        return "TÀI", 90, "3 XỈU liên tiếp, khả năng cao đảo sang TÀI."
    elif chain.endswith("TXTX") or chain.endswith("XTXT"):
        return "TÀI", 80, "Chuỗi đan xen, có thể bẻ sang TÀI."
    else:
        return "XỈU", 65, "Không rõ xu hướng, nghiêng nhẹ về XỈU."

def save_history(phien, du_doan, ket_qua, tong, x1, x2, x3, trang_thai):
    record = {
        'Phien': phien,
        'Du_doan': du_doan,
        'Ket_qua': ket_qua,
        'Trang_thai': trang_thai,
        'Tong': tong,
        'Xuc_xac': [x1, x2, x3]
    }
    try:
        if os.path.exists('history.json'):
            with open('history.json', 'r') as f:
                data = json.load(f)
        else:
            data = []
        data.append(record)
        with open('history.json', 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print('Lỗi lưu:', e)

def send_message(text):
    try:
        bot.send_message(chat_id=GROUP_ID, text=text, parse_mode='HTML')
    except Exception as e:
        print('Lỗi gửi:', e)

def run_bot():
    global is_running
    last_phien = None
    last_du_doan = None

    while True:
        if not is_running:
            time.sleep(5)
            continue
        try:
            res = requests.get(API_URL)
            data = res.json()

            phien = data['Phien']
            if phien == last_phien:
                time.sleep(5)
                continue

            last_phien = phien
            ket_qua = data['Ket_qua']
            tong = data['Tong']
            x1 = data['Xuc_xac_1']
            x2 = data['Xuc_xac_2']
            x3 = data['Xuc_xac_3']

            history.append(data)
            if len(history) > 100:
                history.pop(0)

            chain = ''.join(['T' if h['Ket_qua'] == 'Tài' else 'X' for h in history[-10:]])
            du_doan, tin_cay, chi_tiet = du_doan_theo_chuoi(chain)
            ket_qua_bot = 'ĐÚNG ✅' if last_du_doan and ket_qua.upper() == last_du_doan else 'SAI ❌' if last_du_doan else '—'

            save_history(phien, last_du_doan, ket_qua, tong, x1, x2, x3, ket_qua_bot)

            text = f"""
🤖 <b>BOT EXERCAL EDITION TOOL</b>
━━━━━━━━━━━━━━━━━━━━━━  
🎲 <b>GAME:</b> TÀI XỈU SUNWIN  
━━━━━━━━━━━━━━━━━━━━━━  
📌 <b>Phiên Trước:</b> {phien}  
🎲 <b>Xúc Xắc:</b> {x1} - {x2} - {x3}  
🧮 <b>Tổng:</b> {tong}  
🎯 <b>Kết Quả:</b> {ket_qua.upper()}  
🤖 <b>BOT ĐOÁN:</b> {ket_qua_bot}  
🔗 <b>Chuỗi Gần Nhất:</b> {chain}  
━━━━━━━━━━━━━━━━━━━━━  
🔮 <b>Phiên Tiếp Theo:</b> {phien + 1}  
📊 <b>Dự Đoán TỈ LỆ:</b>  
├─ {'⭕️' if du_doan == 'XỈU' else '❌'} TÀI: {100 - tin_cay}%  
├─ {'⭕️' if du_doan == 'TÀI' else '❌'} XỈU: {tin_cay}%  
✅ <b>Độ Tin Cậy:</b> {tin_cay}%  
📌 <b>KẾT QUẢ DỰ ĐOÁN:</b> {du_doan}  
━━━━━━━━━━━━━━━━━━━━━━  
🕒 Đang chờ phiên tiếp theo...
"""
            send_message(text.strip())
            last_du_doan = du_doan
            time.sleep(5)

        except Exception as e:
            print('Lỗi chính:', e)
            time.sleep(5)

# === TELEGRAM COMMANDS ===
def start(update: Update, context: CallbackContext):
    update.message.reply_text("🤖 Bot đang hoạt động!")

def turn_on(update: Update, context: CallbackContext):
    global is_running
    if update.effective_user.id == ADMIN_ID:
        is_running = True
        update.message.reply_text("✅ Bot đã BẬT.")
    else:
        update.message.reply_text("⛔ Không có quyền.")

def turn_off(update: Update, context: CallbackContext):
    global is_running
    if update.effective_user.id == ADMIN_ID:
        is_running = False
        update.message.reply_text("🛑 Bot đã TẮT.")
    else:
        update.message.reply_text("⛔ Không có quyền.")

def status(update: Update, context: CallbackContext):
    state = "✅ ĐANG CHẠY" if is_running else "🛑 ĐANG TẮT"
    update.message.reply_text(f"🤖 Trạng thái BOT: {state}")

# === FLASK KEEP ALIVE ===
@app.route('/')
def home():
    return "Bot Tài Xỉu đang chạy."

def keep_alive():
    app.run(host='0.0.0.0', port=8080)

# === MAIN ===
if __name__ == '__main__':
    threading.Thread(target=keep_alive).start()

    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("on", turn_on))
    dp.add_handler(CommandHandler("off", turn_off))
    dp.add_handler(CommandHandler("status", status))
    updater.start_polling()

    run_bot()