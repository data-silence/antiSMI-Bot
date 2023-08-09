# importing modules, db engines and long_dialoug_textes from the imports folder
from imports.imports import datetime, bot, pd, re
from imports.config_db import asmi, text, DataBaseMixin
from imports.phrases import start_text, help_text

# importing functions from the scripts folder
from scripts.processors import show_date, show_title_4category, get_user_settings, pick_usernews_dict, \
    show_full_news


def user_digest(username: int, parse_date: str = str(datetime.now().date()), part_number: int = 0):
    """
    Sends the user news digest according to his request and settings
    The date and time interval of the last digest requested by the user are recorded in a separate table in the database
    Направляет пользователю подборку новостей (дайджест) согласно его запроса и настроек
    Дата и временной интервал последнего запрошенного пользователем дайджеста фиксируются в отдельной таблице базы
    """
    input_date = datetime.strptime(parse_date, '%Y-%m-%d').date()
    greeting = {
        1: 'утренняя',
        2: 'дневная',
        3: 'вечерняя',
        4: 'ночная'
    }

    # check for availability of digests at a given time
    if input_date > datetime.now().date() or input_date < datetime.strptime('2022-06-28', '%Y-%m-%d').date():
        bot.send_message(username,
                         f'🤖📗 Вы ввели дату из далёкого будущего или глубокого прошлого, а тут я бессилен')
    else:
        known_users = pd.read_sql('SELECT username FROM users', asmi).username.to_list()
        digestinfo = {'username': username, 'digest_date': parse_date, 'part_number': part_number}
        digestinfo_df = pd.DataFrame(digestinfo, index=[0])

        user_categories, news_amount, is_subscribed, is_header = get_user_settings(username)
        date_df = show_date(parse_date, part_number)

        if username in known_users:
            first_name = pd.read_sql(f"SELECT first_name FROM users WHERE username = '{username}'", asmi).first_name[0]
            user_news_dict = pick_usernews_dict(date_df, username)
            with asmi.begin() as conn:
                conn.execute(
                    text(
                        f"UPDATE user_digest "
                        f"SET part_number='{part_number}', digest_date='{parse_date}' "
                        f"WHERE username = '{username}'"))

        else:
            first_name = username
            user_news_dict = pick_usernews_dict(date_df)
            digestinfo_df.to_sql(name='user_digest', con=asmi, if_exists='append', index=False)

        if part_number != 0:
            my_news = f'🤖: {first_name}, привет!\n\nТвоя {greeting[part_number]} подборка на\n' \
                      f'{datetime.strptime(parse_date, "%Y-%m-%d").strftime("%d %B %Y")}: 👇\n'
        else:
            my_news = f'🤖: {first_name}, привет!\n\nТвоя подборка за\n' \
                      f'{datetime.strptime(parse_date, "%Y-%m-%d").strftime("%d %B %Y")}: 👇\n'

        for i, category in enumerate(user_categories):
            russian_title = \
                pd.read_sql(f"SELECT russian_title FROM categories WHERE category = '{category}'",
                            asmi).russian_title[0]
            emoj = pd.read_sql(f"SELECT emoj FROM categories WHERE category = '{category}'", asmi).emoj[0]
            category_news = show_title_4category(user_news_dict, category)
            if category_news:
                category_title = f'\n{emoj} {i + 1}. {russian_title.capitalize()}:\n'
                my_news += category_title
                for labels, news in category_news.items():
                    my_news += f'{labels}. {news}\n'

        bot.send_message(username, my_news)

        if is_subscribed is False:
            bot.send_message(username,
                             f'📌 По любому заголовку можно получать подробности: \n'
                             f'отправь координаты заголовка через пробел\n'
                             f'("5 7" направит 7-ую новость 5-ой рубрики)')


def get_full_news(username: int, message: str):
    """
    By user requested news coordinate it gives full news and links to it
    По запрошенной пользователем координате новости выдаёт полную новость и ссылки на неё
    """

    digest_date = pd.read_sql(f"SELECT digest_date FROM user_digest WHERE username = '{username}'", asmi).digest_date[
        0]
    digest_part = pd.read_sql(f"SELECT part_number FROM user_digest WHERE username = '{username}'", asmi).part_number[
        0]
    markdown = """*bold text*"""
    try:
        user_categories, news_amount, is_subscribed, is_header = get_user_settings(username)
        category_number, label = map(int, message.split(' '))
        category = user_categories[category_number - 1]
        date_df = show_date(str(digest_date), digest_part)
        if is_subscribed is True:
            user_news_dict = pick_usernews_dict(date_df, username)
        else:
            user_news_dict = pick_usernews_dict(date_df)
        news_title = user_news_dict[category][['title']].loc[label].title
        full_news = show_full_news(user_news_dict, category, label)
        full_digest = f'🤖 {full_news[0]} 🤖\n\n*{news_title}*\n\n{full_news[1].replace(news_title + ". ", "")}' \
                      f'\n\n👇 СМИ и первоисточники 👇'

        bot.send_message(username, full_digest, parse_mode="Markdown")
        regex_url = re.compile('https://t.me/[-_a-z]*$')
        clean_links = [link for link in full_news[2] if
                       not link.startswith(('tg://resolve?domain=', 'https://t.me/+')) and not regex_url.search(link)]
        clean_links = [link.split('?')[0] if not link.startswith('https://www.youtube.com/watch') else link for link
                       in clean_links]
        for link in clean_links:
            bot.send_message(username, link)

    except KeyError:
        bot.send_message(username, f'⚠ Неправильно введена координата новости.\n'
                                   f'📗 Нужно ввести еще раз, или почитать инструкцию к боту (команда "help")')


def redefine_user_settings(username: int, categories_letter: str, news_amount: int) -> pd.DataFrame:
    """
    Overrides user's settings regarding the categories of news they receive and the number of news items they receive
    New user settings are recorded in a separate database or updated

    Переопределяет настройки пользователя в части категорий получаемых им новостей и их количества
    Новые пользовательские настройки записываются в отдельную базу или актуализируются
    """
    subscribed_users = pd.read_sql(f"SELECT username FROM user_settings WHERE is_subscribed is True", asmi)
    subscribed_users = subscribed_users.username.to_list()

    if username in subscribed_users:
        category_df = pd.read_sql(f"SELECT category, russian_title FROM categories", con=asmi)
        new_category = [category_df.category[category_df.russian_title.str.startswith(el.lower())].iloc[0] for el in
                        categories_letter]

        user_settings = pd.read_sql(f"SELECT * FROM user_settings WHERE username = '{username}'", asmi)
        # Переводим все категорию в False, а затем присваиваем True только тем из них, который указал пользователь
        user_settings[['technology', 'science', 'economy', 'entertainment', 'sports', 'society']] = 'False'
        for category in new_category:
            user_settings[category].iloc[0] = True
        user_settings['news_amount'].iloc[0] = news_amount

        is_subscribed = user_settings.is_subscribed.iloc[0]
        news_amount = user_settings.news_amount.iloc[0]
        show_header = user_settings.show_header.iloc[0]
        technology = user_settings.technology.iloc[0]
        science = user_settings.science.iloc[0]
        economy = user_settings.economy.iloc[0]
        entertainment = user_settings.entertainment.iloc[0]
        sports = user_settings.sports.iloc[0]
        society = user_settings.society.iloc[0]
        with asmi.begin() as conn:
            conn.execute(text(
                f"UPDATE "
                f"user_settings "
                f"SET "
                f"is_subscribed='{is_subscribed}', "
                f"news_amount='{news_amount}',"
                f"show_header='{show_header}',"
                f"technology='{technology}', "
                f"science='{science}', "
                f"economy='{economy}', "
                f"entertainment='{entertainment}', "
                f"sports='{sports}', "
                f"society='{society}' "
                f"WHERE "
                f"username = '{username}'"))
        # user_settings.to_sql(name='user_settings', con=asmi, if_exists='append', index=False)
        return user_settings


# Handlers functions
@bot.message_handler(commands=['start'])
def handle_start(message):
    username = message.chat.id
    bot.send_message(username, start_text)


@bot.message_handler(commands=['help'])
def handle_help(message):
    """
    Displays a message with instructions for the bot
    Выводит сообщение с инструкцией к боту
    """
    username = message.chat.id
    bot.send_message(username, help_text)


@bot.message_handler(commands=['subscribe'])
def handle_subscribe(message):
    """
    Collects user information and writes it to the database
    Собирает сведения о пользователе и пишет в базу данных
    """

    username = message.chat.id
    nickname = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    subscribe_date = str(datetime.now().date())
    success_subscribed_text = (f"Успешно подписался, {nickname}, спасибо! ❤\n\n"
                               "Теперь 4 раза в день тебе будет ждать свежая порция новостей.\n\n"
                               "По умолчанию приходит стандартная сводка: \n"
                               "- все типы новостей (кроме политики); \n"
                               "- по три новости в каждой категории.\n\n"
                               "Изменить параметры можно в настройках.\n\n"
                               "Хорошего дня!")

    user_dict = {'username': username, 'nickname': nickname, 'first_name': first_name, 'last_name': last_name,
                 'subscribe_date': subscribe_date}
    user_df = pd.DataFrame(user_dict, index=[0])
    all_users = pd.read_sql(f"SELECT username FROM user_settings", asmi)
    all_users = all_users.username.to_list()
    subscribed_users = pd.read_sql(f"SELECT username FROM user_settings WHERE is_subscribed is True", asmi)
    subscribed_users = subscribed_users.username.to_list()

    # if the user is signing up for the first time | если пользователя подписывается впервые:
    if username not in all_users:
        # Recorded a user in users | Завели пользователя в users
        user_df.to_sql(name='users', con=asmi, if_exists='append', index=False)
        # Recorded the settings for this user, setting them to their default values
        # Завели настройки для этого пользователя, установив их значениями по умолчанию
        default_settings = pd.read_sql(f"SELECT * FROM user_settings WHERE username = 999999999", asmi)
        user_settings = default_settings
        user_settings.username = username
        user_settings.is_subscribed = True
        user_settings.is_timemachine = True
        user_settings.to_sql(name='user_settings', con=asmi, if_exists='append', index=False)
        bot.send_message(username, success_subscribed_text)

    # if the user subscribed earlier, but unsubscribed | если пользователь подписывался раннее, но отписался:
    elif username not in subscribed_users:
        with asmi.begin() as conn:
            conn.execute(text(
                f"UPDATE user_settings SET is_subscribed = True, is_timemachine = True WHERE username = '{username}'"))

        bot.send_message(username, success_subscribed_text)

    # if the user tries to re-subscribe | если пользователь пытается подписаться повторно:
    elif username in subscribed_users:
        bot.send_message(username, f"Вы уже подписаны.")

    else:
        pass


@bot.message_handler(commands=['unsubscribe'])
def handle_unsubscribe(message):
    """
    Unsubscribe from the mailing list by removing the user's participation flag
    Отписка от рассылки путем снятия пользовательского флага об участии в рассылке
    """
    username = message.chat.id
    nickname = message.from_user.username
    subscribed_users = pd.read_sql(f"SELECT username FROM user_settings WHERE is_subscribed is True", asmi)
    subscribed_users = subscribed_users.username.to_list()
    if username in subscribed_users:
        with asmi.begin() as conn:
            conn.execute(text(f"UPDATE user_settings SET is_subscribed = False WHERE username = '{username}'"))

        bot.send_message(username, f"Спасибо что был с нами, {nickname}! Удачи!")


@bot.message_handler(commands=['timemachine'])
def handle_timemachine(message):
    """
    Responsible for subscribing-unsubscribing to the time-machine option
    Отвечает за подписку-отписку на опцию "машина времени"
    """
    username = message.chat.id
    nickname = message.from_user.username
    q = f"SELECT is_timemachine FROM user_settings WHERE username = '{username}'"
    current_status = DataBaseMixin.get(q, asmi)
    try:
        if current_status[0]['is_timemachine'] is True:
            with asmi.begin() as conn:
                conn.execute(text(f"UPDATE user_settings SET is_timemachine = False WHERE username = '{username}'"))
            bot.send_message(username,
                             f"Марти Макфлай себе такого не позволял! Спасибо что были с нами, {nickname}, удачи!")

        elif current_status[0]['is_timemachine'] is False:
            with asmi.begin() as conn:
                conn.execute(text(f"UPDATE user_settings SET is_timemachine = True WHERE username = '{username}'"))
            bot.send_message(username, f"Вперёд, {nickname}! Назад в будущее!")
    except IndexError:
        bot.send_message(username, f"Назад в будущее летают только подписчики, {nickname}! 😉")


@bot.message_handler(commands=['news'])
def handle_news(message):
    """
    Gives the user's digest for the current day
    Отдаёт пользовательскую подборку на текущий день
    """
    username = message.chat.id  # temp_dict автора сообщения
    user_date = str(datetime.now().date())
    user_digest(username, parse_date=user_date, part_number=0)


@bot.message_handler(commands=['settings'])
def handle_settings(message):
    """
    Gives subscribed users instructions on how to change the default settings
    Даёт подписанным пользователям инструкцию по изменению настроек по умолчанию
    """
    username = message.chat.id
    nickname = message.from_user.username

    subscribed_users = pd.read_sql(f"SELECT username FROM user_settings WHERE is_subscribed is True", asmi)
    subscribed_users = subscribed_users.username.to_list()

    if username in subscribed_users:
        settings_text = (f"Стандартная настройка позволяет получать 3 новости без политики.\n"
                         f"А здесь рассказано, как изменить категории и количество новостей в каждой категории.\n"
                         f"📗 Настройка пока сложная, прочти внимательно {nickname}!\n\n"
                         f"🤖 Я умею собирать шесть категорий новостей, каждая из которых начинается со своей буквы:\n"
                         f"Н - Наука\n"
                         f"П - Политика\n"
                         f"О - Общество и развлечения\n"
                         f"С - Спорт\n"
                         f"Т - Технологии и IT\n"
                         f"Э - Экономика\n\n"
                         f""
                         f'Чтобы это изменить, нужно направить мне новые настройки в формате "буквы_слитно" "число"\n'
                         f'Например, "СТЭ 5" позволит получать по пять новостей спорта, технологий и экономики\n'
                         f'Остальные категории будут игнорироваться, пока не изменишь настройки ещё раз\n\n'
                         f'P.S. Название букв можно вводить в любом регистре и последовательности, но только слитно.\n'
                         f' Нельзя послать только буквы или только число')
        bot.send_message(username, settings_text)
    else:
        bot.send_message(username, 'Чтобы получить доступ с настройкам, нужно подписаться')


@bot.message_handler(content_types=['text'])
def guess_user_request(message):
    """
    Tries to guess the user's wishes based on the message received from the user and process the request
    Пытается угадать желания пользователя по полученному от него сообщению
    """
    username = message.chat.id
    answer = message.text
    try:
        valid_date = datetime.strptime(answer, '%Y-%m-%d')
        user_digest(username, parse_date=answer)
    except ValueError:
        try:
            if answer[0].isdigit():
                category_number, label = map(int, answer.split(' '))
                get_full_news(username, answer)
            elif answer[0].isalpha():
                categories_letter = answer.split(' ')[0]
                news_amount = int(answer.split(' ')[1])
                new_user_settings = redefine_user_settings(username, categories_letter, news_amount)
                if type(new_user_settings) == pd.DataFrame and not new_user_settings.empty:
                    bot.send_message(username, 'Новые настройки применены')
                else:
                    bot.send_message(username, 'Что-то пошло не так')

        except ValueError:
            bot.send_message(username,
                             '⚠ Могу обрабатывать только дату (формат ГГГГ-ММ-ДД) или координаты новости (два '
                             'числа через пробел).\n'
                             '📗 Нужно ввести еще раз, или почитать инструкцию к боту (команда "help")')
