from imports.imports import datetime, pd, bot, ApiTelegramException
from imports.config_db import asmi, text

from scripts.handlers import user_digest
from scripts.time_machine import Digest


def sending_fresh_news(part_number):
    """
    Makes periodic digests to subscribed users according to their settings
    Делает периодическую рассылку дайджестов подписавшимся пользователям согласно их настройкам
    """
    subscribed_users_df = pd.read_sql(f"SELECT username FROM user_settings WHERE is_subscribed is True", con=asmi)
    if not subscribed_users_df.empty:
        subscribed_users_dict = subscribed_users_df.T.to_dict()
        parse_date = str(datetime.now().date())
        for users in subscribed_users_dict.values():
            username = users['username']
            try:
                user_digest(username, parse_date, part_number)
            except ApiTelegramException as e:
                if e.description == "Forbidden: bot was blocked by the user":
                    print(f"Пользователь {username} забанил бот.")
                    with asmi.begin() as conn:
                        conn.execute(
                            text(f"UPDATE user_settings SET is_subscribed = False WHERE username = '{username}'"))


def sending_past_news():
    """
    Makes periodic digest mailings to "time machine" subscribers
    Делает периодическую рассылку новостей подписчикам "машины времени"
    """
    digest = Digest()
    for user_id in digest.users_dict:
        user_digest = digest[user_id]
        for year_news in reversed(user_digest):
            bot.send_message(user_id, year_news, parse_mode='html')
    del digest
