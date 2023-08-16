# antiSMI-Bot

![](https://github.com/maxlethal/antiSMI-Bot/blob/master/img/bot_presentation.png?raw=true)

Bot is a telegram interface to personal and smart news aggregator of russian-language media:
- removes news garbage (ads, disclaimers, etc.)
- provides news in neutral-colored and summarized form)
- combines similar news into stories: minimizes viewing of duplicate news stories
- subscriber decides what and how he/she wants to read (categories, quantity, sources)
- subscribers receive short news digests four times a day according to their settings
- there are default settings that allow to use the bot without any actions


Bot uses machine learning models to solve the problem of classification, news clustering, neutral headline and summary generation.

[Bot](https://t.me/antiSMI_bot) is one of three parts of [antiSMI Project](https://github.com/maxlethal/antiSMI-Project"): Parser, Bot and Observer.

## Version history

### [v 1.0](https://github.com/maxlethal/antiSMI-1.0) [complited]
* 15 russian news sources
* collects 6 categories of news: sciense, politics, economy, technology, entertainment, sports
* personal news settings
* personal news digests 4 times a day

### [v 2.0](https://github.com/maxlethal/antiSMI-2.0) [complited]
* expand the number of news sources to 40 [done]
* migrate databases from local Sqlite into remote PostgreSQL [done]
* logging proccess implementation [done]
* dashboards implementation to gets news stats [done] - developing as antiSMI-Monitor

### v 3.0 [in progress]:
* time mashine - get news from the past (5, 10, 20 years ago) [done]
* working remote [done]
* wrapped in docker [done]
* improve news classification model
* improve news summarization model (optional)
* customizing news sources
* news in English, Ukranian and make the necessary models for this
* voice digests


