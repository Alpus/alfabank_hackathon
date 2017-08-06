from collections import defaultdict
from enum import Enum
from functools import wraps

import telebot

from . import settings
from .node import Bank, Client

__all__ = ['bot']

bot = telebot.TeleBot(settings.API_TOKEN)
bank = Bank()


bank_chats = set()
chat_key_mapping = {}
key_to_client = {}
address_to_client = {}
chat_state = defaultdict(lambda: None)

money_sending = defaultdict(lambda: [])
approve = defaultdict(lambda: [])


class NoKeyButtons(Enum):
    GETKEYSPAIR = 'Create keys pair'
    SETKEY = 'Set private key'

class EmulateButtons(Enum):
    EMULATE_BANK = 'Emulate bank account'

class KeyButtons(Enum):
    SENDMONEY = 'Send money'
    BALANCE = 'Show balance'
    EXIT_KEY = 'Reset key'

class BankButtons(Enum):
    SHOW_NOT_APPROVED = 'Show not approved transactions'
    APPROVE = 'Approve transaction'
    EXIT_BANK = 'Stop bank mode'


def make_buttons(buttons_enum):
    return list(map(lambda button_enum: telebot.types.KeyboardButton(button_enum.value), buttons_enum))


def make_markup_by_enums(*enums):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=4)
    for enum in enums:
        markup.add(*make_buttons(enum))

    return markup


def make_simple_markup(chat_id):
    if chat_id in bank_chats:
        markup = make_markup_by_enums(BankButtons)
    elif chat_id not in chat_key_mapping:
        markup = make_markup_by_enums(NoKeyButtons, EmulateButtons)
    else:
        markup = make_markup_by_enums(KeyButtons, NoKeyButtons)

    return markup


def text_to_key(text):
    text = text.replace('AlfaCrypto:\n', '')
    return eval(text)

@bot.message_handler(content_types=['text'])
def send_welcome(message):
    chat_id = message.chat.id
    markup = make_simple_markup(chat_id)
    if message.text == NoKeyButtons.GETKEYSPAIR.value:
        send_keypair(message)
    elif message.text == NoKeyButtons.SETKEY.value:
        send_key_request(message)
    elif message.text == EmulateButtons.EMULATE_BANK.value:
        bank_chats.add(chat_id)
        markup = make_simple_markup(chat_id)
        bot.send_message(chat_id, settings.BANK_EMULATOR, reply_markup=markup)
    elif message.text == BankButtons.EXIT_BANK.value:
        bank_chats.remove(chat_id)
        markup = make_simple_markup(chat_id)
        bot.send_message(chat_id, settings.BANK_EMULATOR_OFF, reply_markup=markup)
    elif message.text == KeyButtons.EXIT_KEY.value:
        del chat_key_mapping[chat_id]
        markup = make_simple_markup(chat_id)
        bot.send_message(chat_id, settings.KEY_DELETED, reply_markup=markup)
    elif message.text == BankButtons.SHOW_NOT_APPROVED.value:
        transactions = bank.get_not_confirmed_transactions()
        bot.send_message(chat_id, 'Addresses and transactions ids:')
        if len(transactions) == 0:
            bot.send_message(chat_id, 'No not approved transactions')
        else:
            for address, ids in transactions.items():
                bot.send_message(chat_id, 'Address:')
                bot.send_message(chat_id, repr(address))
                bot.send_message(chat_id, 'Ids:')
                bot.send_message(chat_id, ', '.join(map(str, sorted(list(ids)))))
        markup = make_simple_markup(chat_id)
        bot.send_message(chat_id, settings.START_MESSAGE, reply_markup=markup)
    elif message.text == BankButtons.APPROVE.value:
        chat_state[chat_id] = BankButtons.APPROVE
        bot.send_message(chat_id, 'Send address')
    elif chat_state[chat_id] == BankButtons.APPROVE:
        approve[chat_id].append(text_to_key(message.text))
        chat_state[chat_id] = 'Send address'
        bot.send_message(chat_id, 'Send id')
    elif chat_state[chat_id] == 'Send address':
        chat_state[chat_id] = None
        markup = make_simple_markup(chat_id)
        try:
            ac = approve[chat_id]
            ac.append(int(message.text))
            bank.confirm_wallet_transaction(ac[0], ac[1])
            bot.send_message(chat_id, 'Approved!', reply_markup=markup)
        except:
            bot.send_message(chat_id, 'Bad id', reply_markup=markup)
        approve[chat_id] = []
    elif message.text == KeyButtons.BALANCE.value:
        show_balance(message)
    elif message.text == KeyButtons.SENDMONEY.value:
        send_money(message)
    elif chat_state[chat_id] == NoKeyButtons.SETKEY:
        key = text_to_key(message.text)
        if key in key_to_client:
            chat_key_mapping[chat_id] = key
            markup = make_simple_markup(chat_id)
            bot.send_message(chat_id, settings.KEY_SET, reply_markup=markup)
        else:
            bot.send_message(chat_id, settings.KEY_NOT_SET, reply_markup=markup)

        chat_state[chat_id] = None
    elif chat_state[chat_id] == KeyButtons.SENDMONEY:
        key = text_to_key(message.text)
        if key in address_to_client:
            money_sending[chat_id].append(address_to_client[key])
            chat_state[chat_id] = settings.ASK_HOW_MUCH
            bot.send_message(chat_id, settings.ASK_HOW_MUCH)
        else:
            chat_state[chat_id] = None
            bot.send_message(chat_id, settings.BAD_ADDRESS)
            bot.send_message(chat_id, settings.START_MESSAGE, reply_markup=markup)
    elif chat_state[chat_id] == settings.ASK_HOW_MUCH:
        try:
            ms = money_sending[chat_id]
            text = message.text
            text = text.replace(',', '.')
            ms.append(float(text))
            ms[0].send_money(ms[1], ms[2])
            bot.send_message(chat_id, settings.MONEY_SENT)
        except:
            money_sending[chat_id] = []
            bot.send_message(chat_id, settings.BAD_NUMBER)
        bot.send_message(chat_id, settings.START_MESSAGE, reply_markup=markup)
    else:
        chat_id = message.chat.id
        markup = make_simple_markup(chat_id)
        bot.send_message(chat_id, settings.START_MESSAGE, reply_markup=markup)


def send_balance(chat_id):
    balance = key_to_client[chat_key_mapping[chat_id]].get_wallet_balance()
    bot.send_message(chat_id, settings.BALANCE.format(balance))


def show_balance(message):
    chat_id = message.chat.id
    send_balance(chat_id)
    markup = make_simple_markup(chat_id)
    bot.send_message(chat_id, settings.START_MESSAGE, reply_markup=markup)


@bot.message_handler(commands=[NoKeyButtons.GETKEYSPAIR.value])
def send_keypair(message):
    chat_id = message.chat.id
    client = Client()
    key_to_client[client.key] = client
    address_to_client[client.address] = client
    markup = make_simple_markup(chat_id)

    bot.send_message(chat_id, 'Private key:')
    bot.send_message(chat_id, repr(client.key))
    bot.send_message(chat_id, 'Address:')
    bot.send_message(chat_id, repr(client.address), reply_markup=markup)


def send_key_request(message):
    chat_id = message.chat.id
    chat_state[chat_id] = NoKeyButtons.SETKEY
    bot.send_message(chat_id, settings.WAIT_FOR_KEY_MESSAGE)


def send_money(message):
    chat_id = message.chat.id
    key = chat_key_mapping[chat_id]
    money_sending[chat_id].append(key_to_client[key])
    chat_state[chat_id] = KeyButtons.SENDMONEY

    bot.send_message(chat_id, settings.ASK_RECIEVER)


@bot.message_handler(content_types=['text'])
def answer_text(message):
    chat_id = message.chat.id

    markup = make_simple_markup(chat_id)
    if chat_state[chat_id] == NoKeyButtons.SETKEY:
        if message.text in key_to_client:
            chat_key_mapping[chat_id] = message.text
            bot.send_message(chat_id, settings.KEY_SET, reply_markup=markup)
        else:
            bot.send_message(chat_id, settings.KEY_NOT_SET, reply_markup=markup)

        chat_state[chat_id] = None
    else:
        bot.send_message(chat_id, settings.START_MESSAGE, reply_markup=markup)
