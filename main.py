import telebot
from telebot import types
from datetime import datetime
from flask import Flask
from threading import Thread
import os

# --- Render Free Tier Port Fix (Flask) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# -----------------------------------------

API_TOKEN = '8436012785:AAEM7JOA3MnXrWiCQkuFa_wkN7XMv-T3x10'
bot = telebot.TeleBot(API_TOKEN)

ADMIN_ID = 566979596 

STAFF_MEMBERS = [
    "Melaku Awoke AHB0602", "Dereje Getnet AHB0651", "Desalegn Minilh AHB0591", 
    "Tewachew Bekele AHB0175", "Admitew Anteneh AHB0163", 
    "Hailemariam Terefe AHB0537", "Tsehay Molla AHB0538"
]

PRODUCTS = ["Account", "USSD/IBMB", "ATM", "Ebirr", "QR", "POS"]
all_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=2)
    for staff in STAFF_MEMBERS:
        markup.add(staff)
    bot.send_message(message.chat.id, "እንኳን ደህና መጡ! ስምዎን ይምረጡ፦", reply_markup=markup)

# --- የሪፖርት ክፍል (በአንድ ላይ የሚደምር እና CIF በኮማ የሚለይ) ---
@bot.message_handler(commands=['report'])
def report_command(message):
    if message.chat.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add("የዛሬ ሪፖርት", "የቀን ገደብ (Filter)")
        msg = bot.send_message(message.chat.id, "የትኛውን ሪፖርት ማየት ይፈልጋሉ?", reply_markup=markup)
        bot.register_next_step_handler(msg, handle_report_choice)
    else:
        bot.send_message(message.chat.id, f"ፈቃድ የለዎትም። የእርስዎ ID: {message.chat.id}")

def handle_report_choice(message):
    if message.text == "የዛሬ ሪፖርት":
        today = datetime.now().strftime("%Y-%m-%d")
        show_final_report(message.chat.id, today, today)
    elif message.text == "የቀን ገደብ (Filter)":
        msg = bot.send_message(message.chat.id, "ቀኑን ያስገቡ። ለምሳሌ፦\nአንድ ቀን ከሆነ: `2026-03-15` \nየቀን ገደብ ከሆነ: `01-01-2026 to 31-01-2026`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_report_dates)

def process_report_dates(message):
    input_text = message.text
    try:
        if " to " in input_text:
            dates = input_text.split(" to ")
            # የኢትዮጵያ ቀን አጻጻፍ (DD-MM-YYYY) ከሆነው ወደ YYYY-MM-DD መቀየር
            start_date = datetime.strptime(dates[0].strip(), "%d-%m-%Y").strftime("%Y-%m-%d")
            end_date = datetime.strptime(dates[1].strip(), "%d-%m-%Y").strftime("%Y-%m-%d")
            show_final_report(message.chat.id, start_date, end_date)
        else:
            target_date = datetime.strptime(input_text.strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
            show_final_report(message.chat.id, target_date, target_date)
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ ስህተት፡ እባክዎ ቀኑን በትክክለኛ ፎርማት ያስገቡ።\nምሳሌ: 01-01-2026 to 31-01-2026")

def show_final_report(chat_id, start_date, end_date):
    summary_data = {} # ዳታውን ለመደመር የሚያገለግል ባዶ ዲክሽነሪ
    found_any = False

    # በሁሉም ቀናት ውስጥ እያለፈ የሚፈለገው ቀን ውስጥ ያሉትን መረጃዎች ይሰበስባል
    for date_key in all_data.keys():
        if start_date <= date_key <= end_date:
            found_any = True
            for staff_name, prods in all_data[date_key].items():
                if staff_name not in summary_data:
                    summary_data[staff_name] = {}
                
                for p_name, p_data in prods.items():
                    if p_name not in summary_data[staff_name]:
                        summary_data[staff_name][p_name] = {'count': 0, 'cifs': []}
                    
                    # ብዛቱን መደመር
                    summary_data[staff_name][p_name]['count'] += p_data['count']
                    # CIF ቁጥሮችን መጨመር
                    summary_data[staff_name][p_name]['cifs'].extend(p_data['cifs'])

    if not found_any:
        bot.send_message(chat_id, f"❌ ለተጠቀሰው የቀን ገደብ ({start_date} - {end_date}) ምንም ዳታ አልተገኘም።")
        return

    # ውጤቱን ወደ ጽሁፍ መቀየር
    report_text = f"📊 **ጠቅላላ ሪፖርት ከ {start_date} እስከ {end_date}**\n"
    report_text += "━━━━━━━━━━━━━━━━━━\n\n"

    for staff_name, prods in summary_data.items():
        report_text += f"👤 **ሰራተኛ፦ {staff_name}**\n"
        for p_name, p_data in prods.items():
            report_text += f"  🔹 {p_name}: {p_data['count']}\n"
            if p_data['cifs']:
                # CIF ቁጥሮችን በኮማ (,) ለይቶ ማሳየት
                report_text += f"  📄 CIF: `{', '.join(p_data['cifs'])}` \n"
        report_text += "--------------------------------\n"

    # ሪፖርቱ በጣም ረጅም ከሆነ ለቴሌግራም መከፋፈል ሊያስፈልግ ይችላል
    if len(report_text) > 4096:
        for x in range(0, len(report_text), 4096):
            bot.send_message(chat_id, report_text[x:x+4096], parse_mode="Markdown")
    else:
        bot.send_message(chat_id, report_text, parse_mode="Markdown")

# --- የተቀረው የዳታ መመዝገቢያ ክፍል ---
@bot.message_handler(func=lambda message: message.text in STAFF_MEMBERS)
def staff_selected(message):
    staff_name = message.text
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=2)
    today = datetime.now().strftime("%Y-%m-%d")
    markup.add(f"ዛሬ ({today})", "ሌላ ቀን")
    msg = bot.send_message(message.chat.id, f"ውድ {staff_name}፣ ቀኑን ይምረጡ፦", reply_markup=markup)
    bot.register_next_step_handler(msg, process_entry_date, staff_name)

def process_entry_date(message, staff_name):
    today = datetime.now().strftime("%Y-%m-%d")
    if "ዛሬ" in message.text:
        chosen_date = today
    else:
        msg = bot.send_message(message.chat.id, "ቀኑን ያስገቡ (YYYY-MM-DD)፦")
        bot.register_next_step_handler(msg, lambda m: show_product_menu(m.chat.id, staff_name, m.text))
        return
    show_product_menu(message.chat.id, staff_name, chosen_date)

def show_product_menu(chat_id, staff_name, chosen_date):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=2)
    for p in PRODUCTS: markup.add(p)
    markup.add("ጨርሻለሁ (Finish)")
    msg = bot.send_message(chat_id, f"📅 ቀን: {chosen_date}\n👤 ሰራተኛ: {staff_name}\n\nምርት ይምረጡ፦", reply_markup=markup)
    bot.register_next_step_handler(msg, handle_product_choice, staff_name, chosen_date)

def handle_product_choice(message, staff_name, chosen_date):
    prod = message.text
    if prod == "ጨርሻለሁ (Finish)":
        bot.send_message(message.chat.id, "✅ መረጃው ተቀምጧል! እናመሰግናለን።")
        return
    
    msg = bot.send_message(message.chat.id, f"የ {prod} ብዛት ያስገቡ፦")
    if prod == "USSD/IBMB":
        bot.register_next_step_handler(msg, ask_cif_ussd, staff_name, chosen_date, prod)
    else:
        bot.register_next_step_handler(msg, save_data, staff_name, chosen_date, prod)

def save_data(message, staff_name, chosen_date, prod):
    try:
        val = int(message.text)
        record_to_db(chosen_date, staff_name, prod, val, [])
        bot.send_message(message.chat.id, f"✅ {prod} ተመዝግቧል!")
        show_product_menu(message.chat.id, staff_name, chosen_date)
    except:
        bot.send_message(message.chat.id, "እባክዎ ቁጥር ብቻ ያስገቡ!")
        show_product_menu(message.chat.id, staff_name, chosen_date)

def ask_cif_ussd(message, staff_name, chosen_date, prod):
    try:
        count = int(message.text)
        msg = bot.send_message(message.chat.id, f"የ {count}ቱንም CIF በኮማ ለይተው ያስገቡ፦")
        bot.register_next_step_handler(msg, save_ussd_data, staff_name, chosen_date, prod, count)
    except:
        bot.send_message(message.chat.id, "ቁጥር ብቻ ያስገቡ!")
        show_product_menu(message.chat.id, staff_name, chosen_date)

def save_ussd_data(message, staff_name, chosen_date, prod, count):
    raw = message.text.replace('\n', ',').replace('.', ',').split(',')
    cifs = [c.strip() for c in raw if c.strip()]
    if len(cifs) != count:
        bot.send_message(message.chat.id, f"⚠️ ስህተት! የ CIF ብዛት እና የገለጹት ብዛት አይመጣጠንም።")
        show_product_menu(message.chat.id, staff_name, chosen_date)
        return
    record_to_db(chosen_date, staff_name, prod, count, cifs)
    bot.send_message(message.chat.id, "✅ USSD ከነ CIF ተመዝግቧል!")
    show_product_menu(message.chat.id, staff_name, chosen_date)

def record_to_db(date, name, prod, count, cifs):
    if date not in all_data: all_data[date] = {}
    if name not in all_data[date]: all_data[date][name] = {}
    if prod not in all_data[date][name]: all_data[date][name][prod] = {'count': 0, 'cifs': []}
    all_data[date][name][prod]['count'] += count
    all_data[date][name][prod]['cifs'].extend(cifs)

if __name__ == "__main__":
    keep_alive() 
    print("ቦቱ እየሰራ ነው...")
    bot.infinity_polling()
