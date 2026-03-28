import requests
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from api_bot import bot_token
from api_bot import api_weather
import pytz
from datetime import datetime
import asyncio
import re

city = "Санкт Петербург"

url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=ru&appid={api_weather}"


# "Мини-база" с таймером погоды
set_time_information = {}

# Словарь на ожидание ввода времени на добавление
set_waiting_word = {}

# Словарь на ожидание ввода времени на удаление
set_waiting_word_for_delete = {}

auto_task_running = False


# Асинхронная функция, информирующая пользователя по команде start о погоде в текущий момент времени
async def weather(update, context):

    # Сбор информации с сайта в json
    weather_data = requests.get(url).json()

    # Словарь с температурами
    temperature = round(weather_data["main"]["temp"])
    temperature_feels = round(weather_data["main"]["feels_like"])

    # Состояние на небе (Облака, дождь, пасмурность и т.д)
    status = weather_data["weather"][0]["description"]

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

        print(f"{now_time.hour}:{now_time.minute}")

        for key, item in set_time_information.items():
            for time_element in item:
                hours, minutes = time_element.split(":")
                formated_hours = int(hours)
                formated_minutes = int(minutes)

                if (
                    now_time.hour == formated_hours
                    and now_time.minute == formated_minutes
                ):

                    # Тут все та же логика, ничего нового
                    weather_data = requests.get(url).json()
                    temperature = round(weather_data["main"]["temp"])
                    temperature_feels = round(weather_data["main"]["feels_like"])
                    status = weather_data["weather"][0]["description"]

                    try:
                        await bot.send_message(
                            chat_id=key,
                            text=f"Здравствуйте! Сейчас в городе {city} - {status}, температура: {str(temperature)}°C, но ощущается как: {str(temperature_feels)}°C.",
                        )

                        print(f"Отправлено {key}")
                    except Exception as e:
                        print(f"Ошибка: {e}")
        await asyncio.sleep(60)


async def text_with_add_time(update, context):

    chat_id = update.effective_chat.id

    # Если флаг ожидания для нас тру:
    if set_waiting_word[chat_id]:

        # Запоминаю, что ввел пользователь в переменную  и правилтьно это форматирую для регулярного выражения
        text_from_user = update.message.text
        text_from_user = text_from_user.strip()
        text_from_user = text_from_user.replace(" ", "")
        text_from_user = text_from_user.split(",")

        regex = "^([01]?[0-9]|2[0-3]):[0-5]?[0-9]$"
        p = re.compile(regex)

        # Список для форматированного времени
        formated_time_from_user = []

        # Проверка на корректность текста
        for time_text in text_from_user:
            m = re.fullmatch(p, time_text)
            if m is None:
                continue
            else:
                formated_time_from_user.append(time_text)

        # Проверка на количество добавленного времени
        if len(formated_time_from_user) > 0:

            text_for_chat = ", ".join(formated_time_from_user)

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"⏳Пожалуйста, подождите! Идет процесс добавления вашего времени⏳",
            )
            await waiting_to_ask(update, context, formated_time_from_user, chat_id)

        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Никакое время не было добавлено. Введите еще раз команду /addtime и попробуйте снова!",
            )
        # Закрываю "ожидание текста"
        set_waiting_word[chat_id] = False


async def waiting_to_ask(update, context, formated_time_from_user, chat_id):

    # Заготовка пустого списка для добавления времени
    formated_time = []

    # Форматирование времени по определенным требованиям: 00:00 > 0:0, 01:00 > 1:0 и т.д.
    for element in formated_time_from_user:
        hours, minutes = element.split(":")
        formated_hours = int(hours)
        formated_minutes = int(minutes)
        final_formated_time = f"{formated_hours}:{formated_minutes}"
        formated_time.append(final_formated_time)

    # Проверка, нет ли в списке одного и того же времени?
    formated_time = list(dict.fromkeys(formated_time))

    # Проверка, есть ли у нас такой пользователь уже с кастомным временем?
    if chat_id in set_time_information:

        list_add_new_time = []

        # Конкретный пользователь
        user_times = set_time_information[chat_id]

        # Берется один элемент из отформатированного времени
        for time_formated in formated_time:

                # Если нету:
            if time_formated not in user_times:
                user_times.append(time_formated)
                list_add_new_time.append(time_formated)

        if not list_add_new_time:
            await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Такое время уже было добавлено ранее!",
        )

        else:
            list_add_new_time_str = ", ".join(list_add_new_time)

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Время: {list_add_new_time_str} добавлено список ваших уведомлений! Не забудьте теперь прописать команду /sub чтобы рассылка начала работать.",
            )

    # Если же у нас нету такого пользователя, то снчала добавим его уникальный user_id
    # чтобы потом знать, к кому обращаться!
    else:
        set_time_information[chat_id] = formated_time

        formated_time = ", ".join(formated_time)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Время: {formated_time} добавлено список ваших уведомлений! Не забудьте теперь прописать команду /sub чтобы рассылка начала работать.",
        )


# Функция, которая отвечает за точечную настройку времени
async def change_time_information(update, context):

    chat_id = update.effective_chat.id

    # Список который специально создается чтобы показать актуальное время на сейчас!
    lst_sorted = []

    if chat_id in set_time_information: # Если пользователь есть в базе с временем:

        for show_time in set_time_information[chat_id]:
            # Если время "стандартное" (XX:XX)
            if len(show_time) == 5:
                    lst_sorted.append(show_time)

            # Если время "не стандартное" (X:XX)
            elif (len(show_time) == 4) and (":" in show_time[:2]):
                    show_time = "0" + show_time
                    lst_sorted.append(show_time)

            # Если время "не стандартное" (XX:X)
            elif (len(show_time) == 4) and (":" in show_time[2:]):
                    show_time = show_time[:3] + "0" + show_time[3]
                    lst_sorted.append(show_time)

            # Если время "не стандартное" (X:X)
            else:
                last_symbol = show_time[2]
                show_time = "0" + show_time[:]
                show_time = show_time[:3] + "0" + last_symbol
                lst_sorted.append(show_time)

            lst_sorted.sort()

            time_information = ", ".join(lst_sorted)

        await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"💬Пожалуйста, укажите время, которое вы хотите добавить? (можно через запятую)💬",
            )
        await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🗓️Ваше время🗓️: {time_information}",
            )

    # Если его нету, то не показываем время которое уже имеется
    else:

        await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"💬Пожалуйста, укажите время, которое хотите добавить? (можно через запятую)💬",
            )

    # Ставлю флаг для ожидания ввода времени на тру:
    set_waiting_word[chat_id] = True


async def remove_time_information(update, context):

    chat_id = update.effective_chat.id

    if chat_id not in set_time_information:

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌Вы не числитесь в базе пользователей по добавленным временам❌",
        )

    elif set_time_information[chat_id] == []:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"⚠️Отсутсвует время, которое можно было бы удалить⚠️",
        )

    else:

        # Список который специально создается чтобы показать время ДРУГ ЗА ДРУГОМ!
        lst_sorted = []

        for show_time in set_time_information[chat_id]:

            # Если время "стандартное" (XX:XX)
            if len(show_time) == 5:
                lst_sorted.append(show_time)

            # Если время "не стандартное" (X:XX)
            elif (len(show_time) == 4) and (":" in show_time[:2]):
                show_time = "0" + show_time
                lst_sorted.append(show_time)

            # Если время "не стандартное" (XX:X)
            elif (len(show_time) == 4) and (":" in show_time[2:]):
                show_time = show_time[:3] + "0" + show_time[3]
                lst_sorted.append(show_time)

            # Если время "не стандартное" (X:X)
            else:
                last_symbol = show_time[2]
                show_time = "0" + show_time[:]
                show_time = show_time[:3] + "0" + last_symbol
                lst_sorted.append(show_time)

        lst_sorted.sort()

        time_information = ", ".join(lst_sorted)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"💬Пожалуйста, укажите время, которое вы хотите удалить? (через запятую)💬",
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🗓️Ваше время🗓️: {time_information}",
        )

        # Ставлю флаг на прослушивание, чтобы удалить время
        set_waiting_word_for_delete[chat_id] = True


# Функция для обработки месадж хандлера под определенные случаи
async def message_navigate(update, context):

    chat_id = update.effective_chat.id

    # Для вызова на добавление
    if set_waiting_word.get(chat_id):
        await text_with_add_time(update, context)

    # Для вызова на удаление
    elif set_waiting_word_for_delete.get(chat_id):
        await process_remove_time(update, context)

    # Для подсказки что команда не найдена
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"⁉️Неизвестная команда⁉️",
        )


async def process_remove_time(update, context):


    chat_id = update.effective_chat.id

    if set_waiting_word_for_delete[chat_id] == True:

        # Запоминаю, что ввел пользователь в переменную
        text_from_user_to_delete = update.message.text

        # Форматирование времени в список: ["09:45", "03:15"]
        text_from_user_to_delete = text_from_user_to_delete.strip()
        text_from_user_to_delete = text_from_user_to_delete.replace(" ", "")
        text_from_user_to_delete = text_from_user_to_delete.split(",")

        regex = "^([01]?[0-9]|2[0-3]):[0-5]?[0-9]$"
        p = re.compile(regex)

        # Заготовка пустого списка для добавления времени на удаление
        formated_time_for_delete = []

        # Проверка на корректность текста
        for time_text in text_from_user_to_delete:
            m = re.fullmatch(p, time_text)
            if m is None:
                continue
            else:
                formated_time_for_delete.append(time_text)

        final_formated_list_delete = []

        # Форматирование времени по определенным требованиям: 00:00 > 0:0, 01:00 > 1:0 и т.д.
        for element in formated_time_for_delete:
            hours, minutes = element.split(":")
            formated_hours = int(hours)
            formated_minutes = int(minutes)
            final_formated_time = f"{formated_hours}:{formated_minutes}"
            final_formated_list_delete.append(final_formated_time)

        # Проверка, нет ли в списке одного и того же времени?
        for element_time in final_formated_list_delete:
            number_of_counter = final_formated_list_delete.count(element_time)
            if number_of_counter != 1:
                final_formated_list_delete.remove(element_time)

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
                text=f"🎯Время: {list_of_deleted_time} успешно удалено!🎯",
            )

        else:

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"❌️Никакое время не было удалено, так как оно отсутсвует!❌️",
            )
        set_waiting_word_for_delete[chat_id] = False


# Функция которая показывает, на какое время у меня поставлено уведомление?
async def show_time_dict(update, context):

    chat_id = update.effective_chat.id

    try:

        text_of_time = set_time_information[chat_id]

    except KeyError:

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"⚠️У вас не имеется ни одного добавленного времени.  Введите /addtime и попробуйте снова⚠️",
        )
        return

    # Список который специально создается чтобы показать добавленное время ДРУГ ЗА ДРУГОМ!
    lst_sorted = []

    for show_time in text_of_time:

        # Если время "стандартное" (XX:XX)
        if len(show_time) == 5:
            lst_sorted.append(show_time)

        # Если время "не стандартное" (X:XX)
        elif (len(show_time) == 4) and (":" in show_time[:2]):
            show_time = "0" + show_time
            lst_sorted.append(show_time)

        # Если время "не стандартное" (XX:X)
        elif (len(show_time) == 4) and (":" in show_time[2:]):
            show_time = show_time[:3] + "0" + show_time[3]
            lst_sorted.append(show_time)

        # Если время "не стандартное" (X:X)
        else:
            last_symbol = show_time[2]
            show_time = "0" + show_time[:]
            show_time = show_time[:3] + "0" + last_symbol
            lst_sorted.append(show_time)

    lst_sorted.sort()

    lst_sorted = ", ".join(lst_sorted)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Время, в которое вам приходят уведомления: {lst_sorted}",
    )


# Когда пользователь вводит команду /auto, его юзер айди добавляется в множество, где потом функция берет его юзерайди и он получает сообщение!
async def start_auto_informated(update, context):


    # Запоминаем его id
    chat_id = update.effective_chat.id

    # Добавляем
    if chat_id in set_time_information:

        if set_time_information.get(chat_id) != []:


            # Список который специально создается чтобы показать добавленное время ДРУГ ЗА ДРУГОМ!
            lst_sorted = []

            for show_time in set_time_information[chat_id]:

                # Если время "стандартное" (XX:XX)
                if len(show_time) == 5:
                    lst_sorted.append(show_time)

                # Если время "не стандартное" (X:XX)
                elif (len(show_time) == 4) and (":" in show_time[:2]):
                    show_time = "0" + show_time
                    lst_sorted.append(show_time)

                # Если время "не стандартное" (XX:X)
                elif (len(show_time) == 4) and (":" in show_time[2:]):
                    show_time = show_time[:3] + "0" + show_time[3]
                    lst_sorted.append(show_time)

                # Если время "не стандартное" (X:X)
                else:
                    last_symbol = show_time[2]
                    show_time = "0" + show_time[:]
                    show_time = show_time[:3] + "0" + last_symbol
                    lst_sorted.append(show_time)

            lst_sorted.sort()

            time_information = ", ".join(lst_sorted)


            # Уведомляем о работе рассылки
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"✅Рассылка будет работать по расписанию: {time_information}✅",
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

        else:
            # Уведомляем о том что времени нету
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Отсутствует время, актуальное для рассылки!",
            )



    else:
        # Пишем, что для этого необходимо сначала создать время
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Для начала добавьте время, чтобы начала работать рассылка: /addtime",
        )


async def stop_information(update, context):

    chat_id = update.effective_chat.id

    if chat_id in set_time_information:
        del set_time_information[chat_id]
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="✅Вы успешно отписались от рассылки!"
        )


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

    # Специальный обработчик который "распределяет время" (удаление, добавление)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_navigate)
    )

    # Запуск бота
    print("Бот запущен")
    application.run_polling()
