from imports.imports import dt, relativedelta, Counter
from imports.config_db import asmi, time_machine, DataBaseMixin

from scripts.processors import news2emb, AgglomerativeClustering


class User:
    """
    Class for collecting and storing user settings
    Класс для сбора и хранения пользовательских настроек подписчиков
    """

    def __init__(self):
        self.subscribed_users = []

    def __len__(self):
        return len(self.subscribed_users)

    @staticmethod
    def __get_users() -> list[dict]:
        """
        Function to retrieve custom settings of time machine subscribers
        Функция для получения пользовательских настроек подписчиков машины времени
        """
        q = f"" \
            f"SELECT nickname, user_settings.username, news_amount, technology, science, economy, entertainment, sports, society " \
            f"FROM user_settings " \
            f"JOIN users ON (user_settings.username=users.username) " \
            f"WHERE is_subscribed is True and is_timemachine is True"
        subscribed_users = DataBaseMixin.get(q, asmi)
        return subscribed_users

    def set_users(self):
        self.subscribed_users = self.__get_users() if not self.subscribed_users else print('Настройки уже собраны')

    @property
    def get_users(self) -> list:
        return self.subscribed_users

    def __getitem__(self, user_id: int) -> tuple[str, int, list[str]]:
        """
        Gives user settings by user id
        Отдаёт настройки пользователя по его id
        """
        if not self.subscribed_users:
            self.set_users()
        subscribed_users = self.get_users
        user_settings = [user for user in subscribed_users if user['username'] == user_id][0]
        nickname = user_settings['nickname']
        news_amount = user_settings['news_amount']
        categories = [category for category, is_subscribed in user_settings.items() if is_subscribed is True]
        return nickname, news_amount, categories


class News(DataBaseMixin):
    """
    A class for collecting and storing user news on a date from the past
    Класс для сбора и хранения пользовательских новостей на дату из прошлого
    """

    def __init__(self, years_ago: int):
        self.years_ago = years_ago
        self.date_news = []
        self.categories_news_dict = {'technology': '', 'science': '', 'economy': '', 'entertainment': '', 'sports': '',
                                     'society': ''}

    def __get_date_news(self) -> list[dict]:
        """
        Gets news on a given date from the past
        Получает новости на заданную дату из прошлого
        """
        now_date = dt.datetime.now().date()
        past_date = now_date - relativedelta(years=self.years_ago)
        q = f"SELECT * FROM news WHERE date::date = '{past_date}'"
        date_news = DataBaseMixin.get(q, time_machine)
        return date_news

    def set_date_news(self):
        self.date_news = self.__get_date_news if not self.date_news else print('Новости уже собраны')

    @property
    def get_date_news(self):
        return self.date_news

    def __get_category_news(self, category: str) -> list[dict]:
        """
        Selects top-news articles of the required category using agglomerative clustering
        Отбирает с помощью агломеративной кластеризации top-новости требуемой категории
        """
        if not self.date_news:
            self.set_date_news()
        date_news = self.get_date_news()
        category_news = [dict(news) for news in date_news if news['category'] == category]
        emb_list = [news2emb(news['news']) for news in category_news]
        model = AgglomerativeClustering(n_clusters=None, metric='cosine', linkage='complete',
                                        distance_threshold=0.3)
        labels = model.fit_predict(list(emb_list))
        # model = MaxDiameterClustering(max_distance=0.05, metric='cosine', precomputed_dist=True)
        # dist_matrix = compute_sparse_dist_matrix(emb_list, metric='cosine')
        # labels = model.fit_predict(dist_matrix)
        for news_number in range(len(category_news)):
            category_news[news_number]['label'] = labels[news_number]
        return category_news

    def get_category_news(self, category: str):
        return self.categories_news_dict[category]

    def set_category_news_item(self, category: str):
        if not self.date_news:
            self.set_date_news()
        if not self.categories_news_dict[category]:
            self.categories_news_dict[category] = self.__get_category_news(category)
        else:
            print(f'Новости {category} уже собраны')

    def __getitem__(self, category):
        """
        Gives the news of the required category through the getter
        Отдаёт новости требуемой категории через геттер
        """
        if not self.date_news or not self.categories_news_dict[category]:
            self.set_category_news_item(category)
        category_news_item = self.get_category_news(category)
        return category_news_item


class Digest:
    """
    A generic class for collecting and storing user digests for past dates specified by a time machine
    Общий класс для сбора и хранения дайджестов пользователей на даты прошлого, заданные машиной времени
    """

    def __init__(self):
        self.my_years = {1: 'год', 3: 'года', 5: 'лет', 10: 'лет', 15: 'лет', 20: 'лет'}
        self.categories_dict = self.define_smi_categories_dict()
        self.users_dict = self.define_user_dict()
        self.news_dict = self.define_news_dict()

    @staticmethod
    def define_smi_categories_dict() -> dict:
        q = f"SELECT * FROM categories"
        base_categories = DataBaseMixin.get(q, asmi)
        smi_categories_dict = {}

        for cat in base_categories:
            trunc_cat_dict = dict(cat)
            del trunc_cat_dict['category']
            smi_categories_dict[cat['category']] = trunc_cat_dict

        return smi_categories_dict

    @staticmethod
    def define_user_dict() -> dict[dict]:
        """
        Creates a dictionary of each user's customization dictionaries
        Создаёт словарь словарей настроек каждого пользователя
        """
        users = User()
        users.set_users()
        user_ids = [user_id['username'] for user_id in users.get_users]
        users_dict = {}
        for user_id in user_ids:
            nickname, news_amount, categories = users[user_id]
            users_dict[user_id] = {'nickname': nickname, 'news_amount': news_amount, 'categories': categories,
                                   'news': {}}
        return users_dict

    def define_news_dict(self) -> dict[int, dict]:
        """
        Creates a dictionary of news dictionaries for each year
        Создаёт словарь словарей новостей для каждого года
        """
        result_news_dict = {}
        for year in self.my_years.keys():
            year_news = News(year)
            category_dict = {}
            for category in self.categories_dict.keys():
                try:
                    category_dict[category] = year_news[category]
                except ValueError:
                    continue
            result_news_dict[year] = category_dict
        return result_news_dict

    def get_result_cluster_news(self, years_ago: int, category: str, amount_news: int) -> list[list]:
        """
        Builds a cluster of news of a certain category for a certain year in the required quantity
        Формирует кластер новостей определенной категории за определенный год в нужном количестве
        """
        final_cluster_news = []
        try:
            category_news = self.news_dict[years_ago][category]
        except KeyError:
            category_news = []
        if category_news:
            most_popular = Counter(news['label'] for news in category_news).most_common(amount_news)
            for label in range(len(most_popular)):
                claster_news = [news for news in category_news if news['label'] == most_popular[label][0]]
                final_cluster_news.append(claster_news)
            result_cluster_news = []
            for label in range(len(most_popular)):
                links = set()
                for news in final_cluster_news[label]:
                    temp_links = set(news['links'].split(','))
                    links.add(news['url'])
                    links = links.union(temp_links)
                max_lenght = max({len(news['news']) for news in final_cluster_news[label]})
                claster_news = [news for news in final_cluster_news[label] if len(news['news']) == max_lenght]
                claster_news[0]['result_links'] = links
                result_cluster_news.append(claster_news)
        else:
            result_cluster_news = []

        return result_cluster_news

    def get_category_digest(self, years_ago: int, categories: list, amount_news: int) -> str:
        """
        Converts the list of news from the get_result_cluster_news function to a digest
        Преобразовывает список новостей из функции get_result_cluster_news в дайджест
        """
        category_digest = ''

        for category in categories:
            result_cluster_news = self.get_result_cluster_news(years_ago=years_ago, category=category,
                                                               amount_news=amount_news)
            if result_cluster_news:
                category_digest += f'\n<b>{self.categories_dict[category]["emoj"]} {self.categories_dict[category]["russian_title"].title()}:</b>'
                for i, news in enumerate(result_cluster_news):
                    for el in range(len(news)):
                        current_news = f'\n{i + 1}. <a href="{news[el]["url"]}">{news[el]["title"]}</a>'
                        category_digest += current_news
                category_digest += '\n'
        return category_digest

    def get_digest(self, user_id: int, years_ago: int) -> str:
        """
        Getter to get a user digest for a specific year
        Геттер для получения дайджеста пользователя за определенный год
        """
        return self.users_dict[user_id]['news'][years_ago]

    def set_news(self, user_id: int):
        """
        Setter to produce a complete digest for an individual user according to their settings
        Сеттер для изготовления полного дайджеста для отдельного пользователя согласно его настроек
        """
        news_amount = self.users_dict[user_id]['news_amount']
        categories = self.users_dict[user_id]['categories']
        nickname = self.users_dict[user_id]['nickname']
        if not self.users_dict[user_id]['news']:
            for years_ago in self.my_years.keys():
                user_year_digest = self.get_category_digest(years_ago=years_ago, categories=categories,
                                                            amount_news=news_amount)
                if user_year_digest:
                    self.users_dict[user_id]['news'][years_ago] = user_year_digest
                else:
                    continue
        else:
            print(f'Дайджест для {nickname} был собран ранее')

    def __getitem__(self, user_id: int) -> list[str]:
        """
        Getter to get the full digest of an individual user according to their settings
        Геттер для получения полного дайджеста отдельного пользователя согласно его настроек
        """
        user_digest = []
        now_date = dt.datetime.now().date()
        if not self.users_dict[user_id]['news']:
            self.set_news(user_id=user_id)
        for years_ago, news in self.users_dict[user_id]['news'].items():
            past_date = now_date - relativedelta(years=years_ago)
            news = f'<b>🏎 {years_ago} {self.my_years[years_ago]} назад - {past_date.strftime("%d %B %Y")} {"💨" * 3} </b>\n' + news
            user_digest.append(news)
        return user_digest
