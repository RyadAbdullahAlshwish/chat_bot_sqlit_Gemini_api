import streamlit as st
from PIL import Image
import google.generativeai as genai
import sqlite3
import json
import tempfile
from gtts import gTTS
import time
from datetime import datetime

#AIzaSyCaGKbFwlwCarUpa4QT9AypStCtKYNJpKo
# إعداد Google Generative

genai.configure(api_key="AIzaSyCaGKbFwlwCarUpa4QT9AypStCtKYNJpKo")
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
    system_instruction=(
        "انت نموذج ذكاء اصطناعي يهتم فقط بالجانب الطبي واعطاء المعلومات والاجابة "
        "عن الاسئلة التي في الجانب الطبي وعن الشخصيات المتعلقة بالمجال الطبي واي معلومة تختص بنفس المجال "
        "اذا كان هناك سؤال خارج هذا المجال عليك ان تجيبه برسالة "
        "'انا اسف لا يمكنني التحدث في مجال اخر. هل تريد المساعدة في الجانب الطبي؟ "
        "لا تتردد في السؤال.'"
    ),
)

# إعداد قاعدة بيانات SQLite
def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute(''' 
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            history TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# دالة لحفظ المحادثة في SQLite
def save_chat(chat_name, chat_history):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("INSERT INTO conversations (name, history) VALUES (?, ?)",
              (chat_name, json.dumps(chat_history)))
    conn.commit()
    conn.close()

# دالة لاسترجاع المحادثات المحفوظة
def get_saved_chats():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT id, name, history FROM conversations")
    chats = c.fetchall()
    conn.close()
    return chats

# دالة لحذف محادثة
def delete_chat(chat_id):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("DELETE FROM conversations WHERE id = ?", (chat_id,))
    conn.commit()
    conn.close()

st.set_page_config(page_title="Chat Bot", page_icon="🤖")
image_path = "C:\\Users\\FR\\Desktop\\ryad\\IMG_5078.jpg"

# إضافة صورة للبوت واسم البوت بجانبها
col1, col2 = st.columns([1, 3])

with col1:
    try:
        image = Image.open(image_path)
        st.image(image, width=125, caption='Eng.Ryad\n771783032')
    except Exception as e:
        st.error(f"لم يتمكن من تحميل الصورة: {e}")

with col2:
    st.markdown("""
        <h1 style='color: #FFFFFF; background-color: #1E90FF; padding: 25px; text-align: center; border-radius: 10px;'>
        *    بـوت الاسئله الطبيه   *</h1>
        <p style='color: #FFFFFF; text-align: center; font-size: 18px; margin: 0; padding: 5px;'>
        أنا بوت تمت برمجـتي من قبل مهندس محـتـرف وانا أخـدم في الـمـجـال الطـبي 
        </p>
    """, unsafe_allow_html=True)

# تلوين الجزء العلوي
st.markdown(
    """
    <style>
    .header {
        background-color: #6A5ACD;
        padding: 15px;
        color: white;
        text-align: center;
        font-size: 24px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    </style>
    <div class="header">مرحـباً بـك في  بوت عالم الاسئله الطبيه </div>
    """,
    unsafe_allow_html=True
)

# بدء جلسة
chat_session = model.start_chat(history=[])

# تهيئة قاعدة البيانات
init_db()

# إعداد الحالة
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'last_question_time' not in st.session_state:
    st.session_state.last_question_time = time.time()
if 'session_active' not in st.session_state:
    st.session_state.session_active = False

# دالة لتحويل النص إلى صوت
def text_to_speech(text):
    tts = gTTS(text=text, lang='ar')
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    tts.save(temp_file.name)
    return temp_file.name

# عرض المحادثات المحفوظة في الشريط الجانبي
st.sidebar.title("المحادثات المحفوظة")
saved_chats = get_saved_chats()
for index, chat in enumerate(saved_chats):
    chat_id, chat_name, _ = chat
    col1, col2 = st.sidebar.columns([4, 1])
    with col1:
        if st.button(chat_name, key=f"chat_{index}"):

            st.session_state.chat_history = json.loads(chat[2])
    with col2:
        if st.button("🗑", key=f"delete_{index}"):
            delete_chat(chat_id)
            st.sidebar.success("تم حذف المحادثة بنجاح!")
            saved_chats = get_saved_chats()

# إنشاء منطقة المحادثة مع إمكانية التوسع العمودي
dark_mode = st.session_state.get('dark_mode', False)

background_color_user = '#005662' if not dark_mode else '#2E2E2E'
background_color_bot = '#004d00' if not dark_mode else '#1C1C1C'
text_color_user = '#FFFFFF' if dark_mode else '#FFFFFF'
text_color_bot = '#FFFFFF' if dark_mode else '#FFFFFF'
time_color = '#FFFFFF'  # اللون الأبيض للوقت

st.markdown("<div style='height: 20px; overflow-y: auto;'>", unsafe_allow_html=True)
for message in st.session_state.chat_history:
    time_stamp = datetime.now().strftime("%H:%M")
    if 'user' in message:
        st.markdown(
            f"<div style='text-align: right; background-color: {background_color_user}; color: {text_color_user}; padding: 15px; margin: 5px; border-radius: 10px; font-size: 16px;'>"
            f"أنت: {message['user']}<br><span style='font-size: 12px; color: {time_color};'>{time_stamp}</span></div>",
            unsafe_allow_html=True)
    if 'bot' in message:
        st.markdown(
            f"<div style='text-align: left; background-color: {background_color_bot}; color: {text_color_bot}; padding: 15px; margin: 5px; border-radius: 10px; font-size: 16px;'>"
            f"البوت: {message['bot']}<br><span style='font-size: 12px; color: {time_color};'>{time_stamp}</span></div>",
            unsafe_allow_html=True)
        audio_file = text_to_speech(message['bot'])
        st.audio(audio_file, format="audio/mp3")

st.markdown("</div>", unsafe_allow_html=True)



# واجهة المستخدم
user_input = st.text_input("اكتب سؤالك هنا:", key="user_input", max_chars=100, help="اكتب هنا...")

# تقسيم الأزرار إلى عمودين
col1, col2 = st.columns([1, 1])
with col1:
    send_button = st.button("إرسال", key="send_button", use_container_width=True)

with col2:
    send_audio_button = st.button("إرسال صوتي", key="send_audio_button", use_container_width=True)

# منطق إرسال الرسالة
if send_button:
    if user_input:
        st.session_state.session_active = True
        response = chat_session.send_message(user_input)
        response_text = response.candidates[0].content.parts[0].text
        st.session_state.chat_history.append({"user": user_input, "bot": response_text})
        st.session_state.last_question_time = time.time()
    else:
        st.warning("يرجى إدخال نص.")

# منطق زر الإرسال الصوتي
if send_audio_button:
    if user_input:
        st.session_state.session_active = True
        audio_file = text_to_speech(user_input)
        st.audio(audio_file, format="audio/mp3")
        st.session_state.chat_history.append({"user": user_input, "bot": "تم إرسال الصوت."})
        st.session_state.last_question_time = time.time()
    else:
        st.warning("يرجى إدخال نص.")

# التحقق إذا كانت قد مرت 3 دقائق منذ آخر سؤال
if st.session_state.session_active and time.time() - st.session_state.last_question_time > 180:
    if st.session_state.chat_history:
        summary_name = user_input[:20] + "..." if user_input else "محادثة جديدة"
        save_chat(summary_name, st.session_state.chat_history)
        st.session_state.chat_history = []  # مسح المحادثة بعد الحفظ
        st.session_state.session_active = False  # إنهاء الجلسة
