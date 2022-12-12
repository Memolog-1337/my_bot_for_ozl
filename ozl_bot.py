import telebot
import xlsxwriter
import json

from utils.parser import MouserPartnumberParser

BOT_TOKEN = '5715891180:AAGrjec6XKj3bNf_LO-dPYdwoBj2dIa9SBE'

CHAT_ID = '208153305'

bot = telebot.TeleBot('5715891180:AAGrjec6XKj3bNf_LO-dPYdwoBj2dIa9SBE')


@bot.message_handler(commands=['start'])
def start(m, res=False):
    # Добавляем две кнопки
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = telebot.types.KeyboardButton('Mouser')
    item2 = telebot.types.KeyboardButton('Параметрика')
    markup.add(item1)
    markup.add(item2)
    bot.send_message(m.chat.id, 'Есть 2 стула', reply_markup=markup)


# Получение сообщений от юзера
@bot.message_handler(content_types=['text'])
def handle_text(message):
    # Если юзер прислал 1, выдаем ему случайный факт
    if message.text.strip() == 'Mouser':
        answer = 'Пришлите документ на обработку Mouser'
    # Если юзер прислал 2, выдаем умную мысль
    elif message.text.strip() == 'Параметрика':
        answer = 'Пришлите документ на обработку Параметрика'
    # Отсылаем юзеру сообщение в его чат
    bot.send_message(message.chat.id, answer)


@bot.message_handler(content_types=['document'])
def handle_docs_photo(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        input_file_name = f'input_{message.chat.id}.xlsx'
        output_file_name = f'output_{message.chat.id}.xlsx'
        base_file_name = f'base_{message.chat.id}.json'
        src = (
            f'D:\\PythonProd\\my_bot_for_ozl\\{input_file_name}'
        )
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)

        workbook = xlsxwriter.Workbook(output_file_name)
        workbook.add_worksheet()
        workbook.close()
        file = {}
        json.dump(file, open(base_file_name, 'w'))

    except Exception as e:
        bot.reply_to(message, e)

    mouser_parser = MouserPartnumberParser(
        input_file_name,
        output_file_name,
        base_file_name
    )
    mouser_parser.get_partnumbers_and_quantities()
    mouser_parser.check_partnumbers_info()

    bot.reply_to(message, 'Пожалуй, я сохраню это')
    f = open(f'D:\\PythonProd\\my_bot_for_ozl\\{output_file_name}', 'rb')
    bot.send_document(message.chat.id, f)
    # удалить все созданные файлы


# Запускаем бота
bot.polling(none_stop=True, interval=0)
