import telebot
from config import *
from telebot import *
from flask import Flask, request
from pyngrok import ngrok, conf
import time
from waitress import serve
import sqlite3
import threading

bot = telebot.TeleBot(TOKEN)

web_server = Flask(__name__)

@web_server.route('/', methods=['POST'])
def webhook():
    if request.headers.get("content-type") == "application/json":
        update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
        bot.process_new_updates([update])
        return "ok", 200
        
# Configuración de la base de datos SQLite
conn = sqlite3.connect('user_topics.db', check_same_thread=False)
cursor = conn.cursor()

# Crear la tabla si no existe
cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_topics (
            chat_id INTEGER PRIMARY KEY,
            user_name TEXT NOT NULL,
            topic_id INTEGER NOT NULL,
            active BOOLEAN DEFAULT 1
        )
    ''')
conn.commit()

# Añadir una variable global para manejar el estado de la conversación
conversation_active = {}

def update_conversation_status(chat_id, status):
    global conversation_active
    conversation_active[chat_id] = status

def is_conversation_active(chat_id):
    global conversation_active
    return conversation_active.get(chat_id, False)

# Guardar o actualizar la información del tema del usuario
def save_user_topic(chat_id, user_name, topic_id):
    conn = sqlite3.connect('user_topics.db')  # Reabrir la conexión
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO user_topics (chat_id, user_name, topic_id, active)
        VALUES (?, ?, ?, 1)
    ''', (chat_id, user_name, topic_id))
    conn.commit()

def update_user_activity(chat_id, is_active):
    conn = sqlite3.connect('user_topics.db')  # Reabrir la conexión
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE user_topics
        SET active = ?
        WHERE chat_id = ?
    ''', (is_active, chat_id))
    conn.commit()

# Obtener la información del tema del usuario
def get_user_topic(chat_id):
    conn = sqlite3.connect('user_topics.db')  # Reabrir la conexión
    cursor = conn.cursor()
    cursor.execute('''
    SELECT topic_id, active FROM user_topics WHERE chat_id = ?
    ''', (chat_id,))
    result = cursor.fetchone()
    return result

def handle_inactivity(chat_id, timeout=300):
    def close_conversation():
        update_user_activity(chat_id, False)
        update_conversation_status(chat_id, False)  # Marcar la conversación como inactiva
        bot.send_message(chat_id, "La conversación ha sido cerrada por inactividad.")
    
    timer = threading.Timer(timeout, close_conversation)
    timer.start()
    return timer

def reset_inactivity_timer(chat_id):
    handle_inactivity(chat_id)  # Reinicia el temporizador de inactividad

# Comando especial para cerrar la conversación
@bot.message_handler(commands=["cerrar_conversacion"])
def close_conversation_command(message):
    chat_id = message.chat.id
    
    user_topic = get_user_topic(chat_id)
    
    if user_topic and user_topic[1]:  # Verifica si la conversación está activa
        update_user_activity(chat_id, False)
        update_conversation_status(chat_id, False)  # Marcar la conversación como inactiva
        bot.send_message(chat_id, "La conversación ha sido cerrada por inactividad.")
    else:
        bot.reply_to(message, "No tienes una conversación activa con un administrador.")


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f'Hola {message.from_user.first_name}, bienvenido este bot fue creado para resolver tus dudas')

@bot.message_handler(commands=["menu"])
def send_menu(message):
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    itembtn1 = types.InlineKeyboardButton('Tutoriales', callback_data='menu_tutoriales')
    itembtn2 = types.InlineKeyboardButton('Página de Rainbow', url='https://h5.rainbowex.life')
    itembtn3 = types.InlineKeyboardButton('Calculadora', url='https://carpicoder.github.io/calculadora-rainbow/')
    itembtn4 = types.InlineKeyboardButton('Hablar con un administrador', callback_data='talk_to_admin')
    itembtn5 = types.InlineKeyboardButton('Cerrar conversación con el administrador', callback_data='close_conversation')
    itembtn6 = types.InlineKeyboardButton('Cerrar bot', callback_data='close_bot')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4, itembtn5, itembtn6)
    bot.send_message(message.chat.id, 'Menú Principal', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == 'menu_tutoriales':
        # Submenú para Tutoriales
        markup = types.InlineKeyboardMarkup(row_width=1)
        tutorial_btn1 = types.InlineKeyboardButton('Como operar', url='https://www.youtube.com/watch?v=V3sXd2jf9bY')
        tutorial_btn2 = types.InlineKeyboardButton('Me equivoque de moneda', url='https://www.youtube.com/watch?v=mgVoXWtzlbg')
        tutorial_btn3 = types.InlineKeyboardButton('Como invitar un amigo', url='https://www.youtube.com/watch?v=7MKASuXlqvo')
        tutorial_btn4 = types.InlineKeyboardButton('Crear clave de google authenticator', url='https://www.youtube.com/watch?v=XdH4z4H9v60')
        tutorial_btn5 = types.InlineKeyboardButton('Crear contraseña de fondos rainbow', url='https://www.youtube.com/watch?v=etNQvA2XgDM')
        tutorial_btn6 = types.InlineKeyboardButton('VIDEOS LEMON', callback_data='video_lemon')
        tutorial_btn7 = types.InlineKeyboardButton('VIDEOS BINANCE', callback_data='video_binance')
        back_btn = types.InlineKeyboardButton('Volver al menú principal', callback_data='go_back')
        markup.add(tutorial_btn1, tutorial_btn2, tutorial_btn3, tutorial_btn4, tutorial_btn5, tutorial_btn6, tutorial_btn7, back_btn)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Tutoriales", reply_markup=markup)
    
    elif call.data == 'video_lemon':
        markup = types.InlineKeyboardMarkup(row_width=1)
        tutorial_btn1 = types.InlineKeyboardButton('Como recargar con red bsc de Lemon a Rainbow', url='https://www.youtube.com/watch?v=XDYAZ5qKVes')
        tutorial_btn2 = types.InlineKeyboardButton('Convertir pesos a USDT', url='https://www.youtube.com/watch?v=4qhXh-hDfMc')
        tutorial_btn3 = types.InlineKeyboardButton('Retiro de Rainbow a Lemon', url='https://www.youtube.com/watch?v=AhK-IglkOKc')
        back_btn = types.InlineKeyboardButton('Volver al menú principal', callback_data='go_back')
        markup.add(tutorial_btn1, tutorial_btn2, tutorial_btn3, back_btn)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="VIDEOS LEMON", reply_markup=markup)
        
    elif call.data == 'video_binance':
        markup = types.InlineKeyboardMarkup(row_width=1)
        tutorial_btn1 = types.InlineKeyboardButton('Comprar USDT en Binance', url='https://www.youtube.com/watch?v=mzBRUholTtY')
        tutorial_btn2 = types.InlineKeyboardButton('Convertir USDT a pesos en Binance', url='https://www.youtube.com/watch?v=IPcNxQBGoqI')
        tutorial_btn3 = types.InlineKeyboardButton('Enviar USDT de Binance a Rainbow', url='https://www.youtube.com/watch?v=CVD76Tsjy7Y')
        tutorial_btn4 = types.InlineKeyboardButton('Retiro de Rainbow a Binance', url='https://www.youtube.com/watch?v=r0NTWrv_Jg0')
        back_btn = types.InlineKeyboardButton('Volver al menú principal', callback_data='go_back')
        markup.add(tutorial_btn1, tutorial_btn2, tutorial_btn3, tutorial_btn4, back_btn)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="VIDEOS BINANCE", reply_markup=markup)

    elif call.data == 'go_back':
        # Regresar al menú principal
        send_menu(call.message)
        
    elif call.data == 'talk_to_admin':
        chat_id = call.message.chat.id
        user_name = call.message.from_user.first_name or call.message.username
    
        user_topic = get_user_topic(chat_id)
        
        if user_topic:
            # Si ya existe un tema, obtener el topic_id existente
            topic_id = user_topic[0]
            update_user_activity(chat_id, True)
            bot.reply_to(call.message, 'Continuando conversación existente con el administrador.')
        else:
           # Crear un nuevo tema en el grupo de administradores
           topic_message = bot.create_forum_topic(GROUP_CHAT_ID, name=f"Chat con {user_name}")
           topic_id = topic_message.message_thread_id
           save_user_topic(chat_id, user_name, topic_id)
           bot.reply_to(call.message, 'Tu tema ha sido creado. Escribe tu mensaje para enviarlo al administrador.')
        
        # Marcar la conversación como activa
        update_conversation_status(chat_id, True)
        
        # Continuar escuchando los mensajes del usuario
        bot.register_next_step_handler(call.message, handle_user_message, topic_id)
    
    elif call.data == 'close_conversation':
        chat_id = call.message.chat.id
        update_user_activity(chat_id, False)
        update_conversation_status(chat_id, False)  # Marcar la conversación como inactiva
        bot.send_message(chat_id, "Has cerrado la conversación con el administrador.")
            
        
    elif call.data == 'close_bot':
        # Cerrar la conversación
        bot.send_message(call.message.chat.id, 'Gracias por usar el bot. ¡Hasta luego!')
        bot.delete_message(call.message.chat.id, call.message.message_id)
        
# Manejo de los mensajes del usuario
def handle_user_message(message, topic_id):
    chat_id = message.chat.id
    
    if not is_conversation_active(chat_id):
        return  # Salir si la conversación ha sido marcada como cerrada
    
    user_name = message.from_user.first_name
    # Enviar el mensaje del usuario al tema del grupo de administradores
    
    user_topic = get_user_topic(chat_id)
    
    if user_topic:
        topic_id, active = user_topic
        if active:
    
            if message.content_type == 'text':
                bot.send_message(GROUP_CHAT_ID, f"{user_name}: {message.text}", message_thread_id=topic_id)
            elif message.content_type == 'photo':
                bot.send_photo(GROUP_CHAT_ID, message.photo[-1].file_id, caption=f"{user_name} envió una foto.", message_thread_id=topic_id)
            elif message.content_type == 'video':
                bot.send_video(GROUP_CHAT_ID, message.video.file_id, caption=f"{user_name} envió un video.", message_thread_id=topic_id)
            elif message.content_type == 'audio':
                bot.send_audio(GROUP_CHAT_ID, message.audio.file_id, caption=f"{user_name} envió un audio.", message_thread_id=topic_id)
            elif message.content_type == 'document':
                bot.send_document(GROUP_CHAT_ID, message.document.file_id, caption=f"{user_name} envió un documento.", message_thread_id=topic_id)
            elif message.content_type == 'voice':
                bot.send_voice(GROUP_CHAT_ID, message.voice.file_id, caption=f"{user_name} envió un mensaje de voz", message_thread_id=topic_id)
            elif message.content_type == 'sticker':
                bot.send_sticker(GROUP_CHAT_ID, message.sticker.file_id, message_thread_id=topic_id)
            reset_inactivity_timer(chat_id)
            
    # Continuar escuchando los mensajes del usuario solo si la conversación sigue activa
    if is_conversation_active(chat_id):
        bot.register_next_step_handler(message, handle_user_message, topic_id)

# Manejo de la respuesta del administrador y reenvío al chat privado del usuario
@bot.message_handler(func=lambda message: message.chat.id == GROUP_CHAT_ID, content_types=['audio', 'photo', 'voice', 'video', 'document',
    'text', 'sticker'])
def handle_admin_reply(message):
    if message.from_user.is_bot:
        return  # Ignora los mensajes enviados por el bot

    topic_id = message.message_thread_id
    cursor.execute('''
    SELECT chat_id FROM user_topics WHERE topic_id = ?
    ''', (topic_id,))
    result = cursor.fetchone()
    
    if result:
        user_chat_id = result[0]
        if message.content_type == 'text':
            bot.send_message(user_chat_id, f"Administrador: {message.text}")
        elif message.content_type == 'photo':
            bot.send_photo(user_chat_id, message.photo[-1].file_id, caption=f"Administrador envió una foto.")
        elif message.content_type == 'video':
            bot.send_video(user_chat_id, message.video.file_id, caption=f"Administrador envió un video.")
        elif message.content_type == 'audio':
            bot.send_audio(user_chat_id, message.audio.file_id, caption=f"Administrador envió un audio.")
        elif message.content_type == 'document':
            bot.send_document(user_chat_id, message.document.file_id, caption=f"Administrador envió un documento.")
        elif message.content_type == 'voice':
            bot.send_voice(user_chat_id, message.voice.file_id, caption=f"Administrador envió un mensaje de voz")
        elif message.content_type == 'sticker':
            bot.send_sticker(user_chat_id, message.sticker.file_id, caption=f"Administrador envió un sticker.")
    else:
        bot.reply_to(message, 'No se encontró un usuario asociado a este tema.')

if __name__ == '__main__':
    bot.set_my_commands([
        types.BotCommand("start", "Bienvenido"),
        types.BotCommand("menu", "Menu"),
        types.BotCommand("cerrar_conversacion", "Cerrar conversación con el administrador")
    ])
    
    print("Bot iniciado")
    conf.get_default().config_path = "./config_ngrok.yml"
    conf.get_default().region = "sa"
    ngrok.set_auth_token(NGROK_TOKEN)
    ngrok_tunel = ngrok.connect(5000, bind_tls=True)
    ngrok_url = ngrok_tunel.public_url
    print("URL NGROK: ", ngrok_url)
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=ngrok_url)
    serve(web_server, host="0.0.0.0", port=5000)