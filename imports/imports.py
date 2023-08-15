"""
Превращение слов в эмбеддинги осуществляется c помощью navec (часть NLP-проекта natasha, 250 000 слов, эмб длиной 300),
обученными на новостном корпусе русскоязычных текстов. Это Glove-эмбеддинги, уменьшенные с помощью квантизации.
Navec покрывает 98% слов в новостных статьях, проблема OOV решается с помощью спецэмбеддинга <unk>.
Эмбеддинг предложений - среднее эмбеддингов его слов, что хорошо работает для кластеризации.
"""

# Common libs:
import re
from collections import Counter

# Date and time libs:
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import datetime as dt

# Schedulers and threads libs:
from apscheduler.schedulers.background import BlockingScheduler
import threading

# DS and NLP libs:
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering
from navec import Navec

# Telegrams libs:
import telebot
from telebot.apihelper import ApiTelegramException

from imports.config_db import TOKEN

bot = telebot.TeleBot(token=TOKEN)

path = 'models/navec.tar'
navec = Navec.load(path)

pd.set_option('mode.chained_assignment', None)  # убирает предупреждения о возможном конфликте в цепочках присвоений
# pd.set_option('max_colwidth', 120)
# pd.set_option('display.width', 500)
