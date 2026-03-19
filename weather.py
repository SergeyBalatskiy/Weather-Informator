import requests
from telegram.ext import ApplicationBuilder, CommandHandler
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
    application.add_handler(CommandHandler("start", weather))
    application.add_handler(CommandHandler("sub", start_auto_informated))
    application.add_handler(CommandHandler("uns", stop_information))

    print("Бот запущен")
    application.run_polling()
