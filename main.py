import threading
import time

import telebot

from bot import bot
from storage import create_user, users_by_id, message_queue
import states


def try_create_user(user: telebot.types.User):
    if user.id not in users_by_id:
        new_user = create_user(user.id, user.username, f'{user.first_name} {user.last_name}')
        for user in users_by_id.values():
            bot.send_message(user.id, f'Добавлен новый пользователь: {new_user}')


@bot.message_handler(commands=["start"])
def start(message: telebot.types.Message):
    try_create_user(message.from_user)
    states.show_main_menu(users_by_id[message.from_user.id], 'Что вы делаете в моем холодильнике?')


@bot.message_handler(content_types=["text"])
def handle_text(message: telebot.types.Message):
    try_create_user(message.from_user)
    user = users_by_id[message.from_user.id]
    state = states.map_states[user.state.state]
    state.process_message(user, message)


@bot.callback_query_handler(func=lambda callback: True)
def callback_handler(callback: telebot.types.CallbackQuery):
    user = users_by_id[callback.from_user.id]
    state = states.map_states[user.state.state]
    state.process_button(user, callback)


def process_message_queue():
    while True:
        time_to_send, message = message_queue.get()
        current_time = time.time()
        if current_time < time_to_send:
            time.sleep(time_to_send - current_time)
        head = f'Сообщение от {users_by_id[message.from_user_id]}\n'
        bot.send_message(message.to_user_id, head + message.body)


threading.Thread(target=process_message_queue, daemon=True).start()

bot.polling(none_stop=True, interval=0)
