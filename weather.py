import requests
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from api_bot import bot_token
from api_bot import api_weather
from translate import Translator
import pytz
from datetime import datetime
import asyncio


city = "Санкт Петербург"

url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=ru&appid={api_weather}"

# "Мини-база" с пользователями
set_users = set()

# "Мини-база" с таймером погоды
set_time_information = {}

set_waiting_word = {}

auto_task_running = False


# Асинхронная функция, информирующая пользователя по команде start о погоде в текущий момент времени
async def weather(update, context):

    # Сбор информации с сайта в json
    weather_data = requests.get(url).json()

    # Словарь с температурами
    temperature = round(weather_data["main"]["temp"])
    temperature_feels = round(weather_data["main"]["feels_like"])

    # Состояние на небе (Облака, дождь, пасмурность и т.д)
    status = weather_data["weather"][0]["main"]

    # Переводчик состояния с ENG на RU
    translator = Translator(from_lang="en", to_lang="ru")

    # Перезапись на RU
    status = translator.translate(status)

    # Информирование пользователя
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Привет! Сейчас в городе {city} - {status}, температура: {str(temperature)}°C, но ощущается как: {str(temperature_feels)}°C",
    )


# Асинхронная функция, действующая по расписанию! 07:00, 17:00
async def weather_informated(context):
    """Это ужасное тело функции включает в себя много гемороя, но если вкратце, то тут она запускается
    с помощью другой функции start_auto_informated, при этом нужно, чтобы пользователь сначала ввел
    авторизацию /auto, а потом уже в бесконечном цикле проверяется, соответсвтует ли время/час условию?
    """

    print("Функция weather_informated запущена!")

    # Необходимая переменная bot
    bot = context.bot
    time_zone = pytz.timezone("Europe/Moscow")

    while True:
        now_time = datetime.now(time_zone)
        await asyncio.sleep(7)
        if now_time.hour == 7 and now_time.minute == 00:

            # Тут все та же логика, ничего нового
            weather_data = requests.get(url).json()
            temperature = round(weather_data["main"]["temp"])
            temperature_feels = round(weather_data["main"]["feels_like"])
            status = weather_data["weather"][0]["main"]
            translator = Translator(from_lang="en", to_lang="ru")
            status = translator.translate(status)

            # Проверяет, есть ли юзер айди в "множестве", если есть хоть кто то, то сообщение будет получено
            for chat_id_user in list(set_users):
                try:
                    await bot.send_message(
                        chat_id=chat_id_user,
                        text=f"Доброе утро! Сейчас в городе {city} - {status}, температура: {str(temperature)}°C, но ощущается как: {str(temperature_feels)}°C ",
                    )
                    print(f"Отправлено {chat_id_user}")
                except Exception as e:
                    print(f"Ошибка: {e}")
                    if chat_id_user in set_users:
                        set_users.remove(chat_id_user)
            # После отправки сообщения, уходим в спячку на оставуюся минуту!
            await asyncio.sleep(65)

        elif now_time.hour == 17 and now_time.minute == 00:

            # Та же логика, ничего нового
            weather_data = requests.get(url).json()
            temperature = round(weather_data["main"]["temp"])
            temperature_feels = round(weather_data["main"]["feels_like"])
            status = weather_data["weather"][0]["main"]
            translator = Translator(from_lang="en", to_lang="ru")
            status = translator.translate(status)

            for chat_id_user in list(set_users):
                try:
                    await bot.send_message(
                        chat_id=chat_id_user,
                        text=f"Добрый вечер! Сейчас в городе {city} - {status}, температура: {str(temperature)}°C, но ощущается как: {str(temperature_feels)}°C ",
                    )
                    print(f"Отправлено {chat_id_user}")
                except Exception as e:
                    print(f"Ошибка: {e}")
                    if chat_id_user in set_users:
                        set_users.remove(chat_id_user)

            await asyncio.sleep(65)

async def text_with_add_time(update, context):
        
        chat_id = update.effective_chat.id

        # Если флаг ожидания для нас тру:
        if set_waiting_word[chat_id]:

            # Запоминаю, что ввел пользователь в переменную
            text_from_user = update.message.text

            # Вызываю функцию, которая проверяет валидность данных времени
            await check_what_input(text_from_user)

async def check_what_input(text_from_user):







        




async def waiting_to_ask(update, context):

        if set_waiting_word[chat_id] == True:

        # Отладка на всякий случай
        print("Пользователь ввел: ", text_from_user)

        # Форматирование времени в список: ["09:45", "03:15"]
        text_formated = text_from_user.split(", ")

        # Заготовка пустого списка для добавления времени
        formated_time = []

        # Форматирование времени по определенным требованиям: 00:00 > 0:0, 01:00 > 1:0 и т.д.
        for element in text_formated:
            if element[0] == "0":
                element = element[1:5]
                if element[2] == "0":
                    element = element[0:2] + element[3:]
                    formated_time.append(element)
                else:
                    formated_time.append(element)

            elif element[3] == "0":
                element = element[:3] + element[4:]
                formated_time.append(element)

            else:
                formated_time.append(element)

        # Проверка, нет ли в списке одного и того же времени?
        for element_time in formated_time:
            number_of_counter = formated_time.count(element_time)
            if number_of_counter != 1:
                formated_time.remove(element_time)

        # Проверка, есть ли у нас такой пользователь уже с кастомным временем?
        if chat_id in set_time_information:

            list_add_new_time = []
            
            # Проверка, есть ли попытка добавить одно и то же время непосредственно в сам словарь?
            for key, item in set_time_information.items():

                # Берется один элемент из отформатированного времени
                for time_formated in formated_time:

                    # Если уже есть:
                    if time_formated in item:

                        # Пропускаем
                        continue

                    # Или же 
                    else:
                        
                        # Добавляем элемент
                        item.append(time_formated)
                        list_add_new_time.append(time_formated)

            list_add_new_time = ", ".join(list_add_new_time)

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f'Время: {list_add_new_time} добавлено список ваших уведомлений!',
            )

        # Если же у нас нету такого пользователя, то снчала добавим его уникальный user_id
        # чтобы потом знать, к кому обращаться! 
        else:
            set_time_information[chat_id] = formated_time

            formated_time = ", ".join(formated_time)

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f'Время: {formated_time} добавлено список ваших уведомлений!',
            )


# Функция, которая отвечает за точечную настройку времени
async def change_time_information(update, context):
    
    chat_id = update.effective_chat.id

    await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'Пожалуйста, укажите время, когда вы хотите получать информацию о погоде! (можно через ", ")',
        )
    
    # Ставлю флаг для ожидания ввода времени на тру:
    set_waiting_word[chat_id] = True

    

async def remove_time_information(update, context):

    chat_id = update.effective_chat.id

    if chat_id not in set_time_information:

        await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f'Вы не числитесь в базе пользователей по добавленным временам',
            )
    
    elif set_time_information[chat_id] == []:
        await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f'Отсутсвует время, которое можно было бы удалить',
            )

    else:

        await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f'Пожалуйста, укажите время, которое вы хотите удалить? (можно через " ,")',
                )
        
        # Запоминаю, что ввел пользователь в переменную
        text_from_user_to_delete = update.message.text

        # Отладка на всякий случай
        print("Пользователь ввел для удаления: ", text_from_user_to_delete)

        # Форматирование времени в список: ["09:45", "03:15"]
        text_formated_for_delete = text_from_user_to_delete.split(", ")

        # Заготовка пустого списка для добавления времени
        formated_time_for_delete = []

        # Форматирование времени по определенным требованиям: 00:00 > 0:0, 01:00 > 1:0 и т.д.
        for element in text_formated_for_delete:
            if element[0] == "0":
                element = element[1:5]
                if element[2] == "0":
                    element = element[0:2] + element[3:]
                    formated_time_for_delete.append(element)
                else:
                    formated_time_for_delete.append(element)

            elif element[3] == "0":
                element = element[:3] + element[4:]
                formated_time_for_delete.append(element)

            else:
                formated_time_for_delete.append(element)

        # Проверка, нет ли в списке одного и того же времени?
        for element_time in formated_time_for_delete:
            number_of_counter = formated_time_for_delete.count(element_time)
            if number_of_counter != 1:
                formated_time_for_delete.remove(element_time)

        # Счетчик для информирования (дальнейшего)
        list_of_deleted_time = []
        cnt = 0
        # Проверяю, есть ли вообще такое время?
        for element_to_delete in formated_time_for_delete:
            
            # Если элемент у нас есть, то удаляем!
            if element_to_delete in set_time_information[chat_id]:
                set_time_information[chat_id].remove(element_to_delete)
                cnt += 1
                list_of_deleted_time.append(element_to_delete)

            else:
                continue
        
        if cnt > 0:
            list_of_deleted_time = ", ".join(list_of_deleted_time)
            await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f'Время: {list_of_deleted_time} успешно удалено!',
                )
        
        else:

            await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f'Никакое время не было удалено, так как оно отсутсвует!',
                )

# Функция которая показывает, на какое время у меня поставлено уведомление?
async def show_time_dict(update, context):

    chat_id = update.effective_chat.id

    text_of_time = set_time_information[chat_id]

    await context.bot.send_message(chat_id=update.effective_chat.id, text = text_of_time)

# Когда пользователь вводит команду /auto, его юзер айди добавляется в множество, где потом функция берет его юзерайди и он получает сообщение!
async def start_auto_informated(update, context):

    # Запоминаем его id
    chat_id = update.effective_chat.id

    # Добавляем
    if chat_id not in set_users:

        set_users.add(chat_id)

        # Пишем, что рассылка гарантированно будет работать!
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Рассылка запущена!",
        )

        # Информируем о успешном добавлении
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Успешно добавлен новый пользователь! Информирование о погоде по расписанию в: 07:00, 17:00",
        )
        print(set_users)
    else:
        # Пишем, что рассылка гарантированно будет работать!
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Рассылка уже запущена!",
        )

    # Глобализирую важную переменную
    global auto_task_running

    if not auto_task_running:
        auto_task_running = True
        asyncio.create_task(weather_informated(context))
        print("Цикл рассылки запущен")

    """Вся загвоздка заключается в том, что мне необходимо чтобы был бесконечный цикл, но если я 
    сделаю просто через while, то остальной функционал работать не будет, так как будет зациклен.
     ЕСЛИ написать в самом теле функции без глобалки  auto_task_running = True, так тоже работать
     не будет потому что у нас получится так что можно создавать неогр. кол-во функций, а это не
     стоит того! Поэтому это работает так - на первый раз - тру, на второй, третий и т.д - уже 
     все, заново рассылку запускать не получится! ОНА ОДНА! в этом и прикол с глобализацией"""


async def stop_information(update, context):
    chat_id = update.effective_chat.id

    if chat_id in set_users:
        set_users.remove(chat_id)
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Вы успешно отписались от рассылки!"
        )
        print(set_users)

    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Вы не состоите в рассылке!"
        )


if __name__ == "__main__":

    TOKEN = bot_token

    application = ApplicationBuilder().token(TOKEN).build()

    # СТАРТТТТ!
    application.add_handler(CommandHandler("start", weather))

    # Подписываемся на рассылку
    application.add_handler(CommandHandler("sub", start_auto_informated))

    # Отказываемся от рассылки
    application.add_handler(CommandHandler("uns", stop_information))

    # Добавляем время
    application.add_handler(CommandHandler("addtime", change_time_information))

    # Удаляем время
    application.add_handler(CommandHandler("removetime", remove_time_information))

    # Показываем список со всем добавленным временем
    application.add_handler(CommandHandler("showtime", show_time_dict))

    # Специальный обработчик который слушает только текст (он сделан для добавления времени)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_with_add_time))

    # Запуск бота
    print("Бот запущен")
    application.run_polling()
