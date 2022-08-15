import time

import telebot

from bot import bot
from storage import find_user_by_username, users_by_id, User, State, users_by_username, change_state, send_message


class AbstractState:
    @staticmethod
    def process_message(user: User, message: telebot.types.Message):
        raise NotImplementedError()

    @staticmethod
    def process_button(user: User, callback: telebot.types.CallbackQuery):
        if callback.data == 'users':
            response = 'Доступные пользователи:\n'
            for another_user in users_by_id.values():
                response += f'@{another_user.username} {another_user.name}\n'
            bot.send_message(user.id, response)


def show_main_menu(user: User, message: str):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton('Пользователи', callback_data='users'))
    keyboard.add(telebot.types.InlineKeyboardButton('Отправить сообщение', callback_data='send_message'))
    bot.send_message(user.id, message, reply_markup=keyboard)


class IdleState(AbstractState):
    @staticmethod
    def process_message(user: User, message: telebot.types.Message):
        show_main_menu(user, 'Сейчас вы никому не пишете')

    @staticmethod
    def process_button(user: User, callback: telebot.types.CallbackQuery):
        AbstractState.process_button(user, callback)
        if callback.data == 'send_message':
            state = State.CHOOSE_RECEIVER
            change_state(user, state, None, None)
            bot.send_message(user.id, 'Напишите, @кому отправить сообщение')


class ChooseReceiverState(AbstractState):
    @staticmethod
    def parse_username(text: str):
        if not text.startswith('@'):
            return None, 'Имя пользователя должно начинаться с символа @'
        if len(text.split()) > 1:
            return None, 'Имя пользователя не должно содержать пробелов'
        username = text[1:]
        find_user_by_username(username)
        if username not in users_by_username:
            return None, 'Пользователь не найден'
        return users_by_username[username].id, None

    @staticmethod
    def process_message(user: User, message: telebot.types.Message):
        to_user_id, message = ChooseReceiverState.parse_username(message.text)
        if not to_user_id:
            bot.send_message(user.id, message)
        else:
            state = State.MAKE_MESSAGE
            change_state(user, state, to_user_id, None)
            bot.send_message(user.id, 'Напишите сообщение')


class MakeMessageState(AbstractState):
    @staticmethod
    def process_message(user: User, message: telebot.types.Message):
        state = State.SET_DELAY
        change_state(user, state, user.state.message.to_user_id, message.text)
        keyboard = telebot.types.InlineKeyboardMarkup()
        for description, delay in [['Мгновенно', 0],
                                   ['10 секунд', 10],
                                   ['1 минута', 60],
                                   ['5 минут', 300],
                                   ['1 час', 3600]]:
            keyboard.add(telebot.types.InlineKeyboardButton(description, callback_data=f'delay={delay}'))
        bot.send_message(user.id, 'Выберете время задержки или напишите свое в секундах', reply_markup=keyboard)


class SetDelayState(AbstractState):
    @staticmethod
    def parse_delay(text: str):
        if not text.isdigit():
            return None, 'Некорректный формат числа'
        delay = int(text)
        if delay < 0:
            return None, 'Время задержки не может быть отрицательным'
        return delay, None

    @staticmethod
    def send_with_delay(user: User, delay: int):
        time_to_send = int(time.time()) + delay
        send_message(user, time_to_send)
        state = State.IDLE
        change_state(user, state, None, None)
        show_main_menu(user, 'Сообщение отправлено')

    @staticmethod
    def process_message(user: User, message: telebot.types.Message):
        delay, message = SetDelayState.parse_delay(message.text)
        if not delay:
            bot.send_message(user.id, message)
        else:
            SetDelayState.send_with_delay(user, delay)

    @staticmethod
    def process_button(user: User, callback: telebot.types.CallbackQuery):
        AbstractState.process_button(user, callback)
        if callback.data.startswith('delay'):
            delay = int(callback.data.split('=')[1])
            SetDelayState.send_with_delay(user, delay)


map_states = {
    State.IDLE: IdleState,
    State.CHOOSE_RECEIVER: ChooseReceiverState,
    State.SET_DELAY: SetDelayState,
    State.MAKE_MESSAGE: MakeMessageState
}
