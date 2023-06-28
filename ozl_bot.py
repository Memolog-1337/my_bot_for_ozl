import telebot
import xlsxwriter
import json
import traceback

from utils.parser import (
    MouserPartnumberParser,
    KompelParametricaParser,
    PromelectronicaParser,
    LcscParser
)
from utils.parametrica import Parametrica

import utils.searcher as bd

BOT_TOKEN = ''

CHAT_ID = ''

# PATH_TO_CSV: str = ''
PATH_TO_CSV: str = ''
bot = telebot.TeleBot('')

status = ''


@bot.message_handler(commands=['start'])
def start(m, res=False):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = telebot.types.KeyboardButton('Mouser')
    item2 = telebot.types.KeyboardButton('Параметрика')
    item3 = telebot.types.KeyboardButton('Промэлектроника')
    item4 = telebot.types.KeyboardButton('LCSC')
    markup.add(item1)
    markup.add(item2)
    markup.add(item3)
    markup.add(item4)
    bot.send_message(m.chat.id, 'Есть 4 стула', reply_markup=markup)


@bot.message_handler(commands=['search'])
def search(message):
    bot.send_message(message.chat.id, 'Пришлите производителя')    
    bot.register_next_step_handler(message, get_data)


def get_data(message):   
    result = bd.get_data_from_db(message.text.strip())
    if len(result) > 4095:        
        for x in range(0, len(result), 4095):
            bot.send_message(message.chat.id, result[x:x + 4095])    
    else:
        bot.send_message(message.chat.id, result)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    global status

    if message.text.strip() == 'Mouser':
        status = message.text.strip()
        answer = 'Пришлите документ на обработку Mouser'

    elif message.text.strip() == 'Параметрика':
        status = message.text.strip()

    elif message.text.strip() == 'Промэлектроника':
        status = message.text.strip()

    elif message.text.strip() == 'LCSC':
        status = message.text.strip()

    bot.send_message(message.chat.id, answer)


@bot.message_handler(content_types=['document'])
def handle_docs_photo(message):
    global status

    if status == 'Mouser':
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        input_file_name = f'mouser_input_{message.chat.id}.xlsx'
        output_file_name = f'mouser_output_{message.chat.id}.xlsx'
        base_file_name = f'mouser_base_{message.chat.id}.json'
        with open(input_file_name, 'wb') as new_file:
            new_file.write(downloaded_file)

        workbook = xlsxwriter.Workbook(output_file_name)
        workbook.add_worksheet()
        workbook.close()
        file = {}
        json.dump(file, open(base_file_name, 'w'))

        try:
            mouser_parser = MouserPartnumberParser(
                input_file_name,
                output_file_name,
                base_file_name
            )
            mouser_parser.get_partnumbers_and_quantities()
            mouser_parser.check_partnumbers_info()

        except Exception as e:
            bot.reply_to(message, 'Напишите Дане, произошла ошибка' + str(e))
            print('Ошибка:\n', traceback.format_exc())

    elif status == 'Параметрика':
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        input_file_name = f'kompel_input_{message.chat.id}.xlsx'
        output_file_name = f'kompel_output_{message.chat.id}.xlsx'
        base_file_name = f'kompel_base_{message.chat.id}.json'
        with open(input_file_name, 'wb') as new_file:
            new_file.write(downloaded_file)

        workbook = xlsxwriter.Workbook(output_file_name)
        workbook.add_worksheet()
        workbook.close()

        parametrica_file_name = f'parametrica_{message.chat.id}.xlsx'

        workbook = xlsxwriter.Workbook(parametrica_file_name)
        workbook.add_worksheet('TDSheet')
        workbook.close()

        try:
            parametrica = Parametrica(
                input_file_name,
                parametrica_file_name,
                'utils/data_res.json',
                'utils/data_cap.json'
            )
            parametrica.check_parametrica()
            kompel_parser = KompelParametricaParser(
                parametrica_file_name,
                output_file_name,
                base_file_name
            )
            kompel_parser.get_partnumbers_and_quantities()
            kompel_parser.check_purtnumbers_info_kompel()

            f = open(PATH_TO_CSV, 'rb')
            bot.send_document(
                message.chat.id,
                f,
                caption='Это можно выгрузить в Компэл для проверки'
            )

        except Exception as e:
            bot.reply_to(message, 'Напишите Дане, произошла ошибка' + str(e))
            print('Ошибка:\n', traceback.format_exc())

    elif status == 'Промэлектроника':
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        input_file_name = f'prom_input_{message.chat.id}.xlsx'
        output_file_name = f'prom_output_{message.chat.id}.xlsx'
        base_file_name = f'prom_base_{message.chat.id}.json'
        with open(input_file_name, 'wb') as new_file:
            new_file.write(downloaded_file)

        workbook = xlsxwriter.Workbook(output_file_name)
        workbook.add_worksheet()
        workbook.close()

        try:
            prom_parser = PromelectronicaParser(
                input_file_name,
                output_file_name,
                base_file_name
            )
            prom_parser.get_partnumbers_and_quantities()
            prom_parser.check_partnumbers_info_prom()

        except Exception as e:
            bot.reply_to(message, 'Напишите Дане, произошла ошибка' + str(e))
            print('Ошибка:\n', traceback.format_exc())

    elif status == 'LCSC':
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        input_file_name = f'lcsc_input_{message.chat.id}.xlsx'
        output_file_name = f'lcsc_output_{message.chat.id}.xlsx'
        base_file_name = f'lcsc_base_{message.chat.id}.json'
        with open(input_file_name, 'wb') as new_file:
            new_file.write(downloaded_file)

        workbook = xlsxwriter.Workbook(output_file_name)
        workbook.add_worksheet()
        workbook.close()

        try:
            lcsc_parser = LcscParser(
                input_file_name,
                output_file_name,
                base_file_name
            )
            lcsc_parser.get_partnumbers_and_quantities()
            lcsc_parser.check_partnumbers_info_lcsc()

        except Exception as e:
            bot.reply_to(message, 'Напишите Дане, произошла ошибка' + str(e))
            print('Ошибка:\n', traceback.format_exc())

    f = open(output_file_name, 'rb')
    bot.send_document(message.chat.id, f)
    # удалить все созданные файлы


# Запускаем бота
while True:
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print(e)
