from flask import Flask, request
import logging
import json
import requests
from list_words import all_w
import random
import re

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s %(levelname)s %(name)s %(message)s')

stages = [
    '1652229/b8776d321187e6dcfcab',
    '997614/76679b5e78d5952dda81',
    '1521359/6ec251b7a78a9752b898',
    '1540737/47d2a5226be745e5fc59',
    '1652229/0e51e3f19e085b847037',
    '997614/bfca7231ff54987680af',
    '1540737/1234a696560907dee7a1',
    '1652229/f3fbca79435cc4a31ae7'
]

agree = ['да', 'давай', 'можно', 'буду']
disagree = ['нет', 'не хочу', 'не буду', 'не']
stop = ['прекрати', 'закончи', 'хватит', 'завершить', 'закончи', 'закрой', 'закрыть']
sessionStorage = {}

rules = 'Я загадываю слово из категории, которую ты выбрал, а ты должен его угадать! \n\
        У тебя есть 8 прав на ошибку. Ты можешь вводить по одной букве, а, если уже догадался, \
        введи все слово.\nТы можешь ввести слово "виселица" и увидишь состояние виселицы на данный момент. \n\
        Также, если надоело играть, то просто напиши "завершить". Продолжить игру?'

@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)

    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    handle_dialog(response, request.json)

    logging.info('Request: %r', response)

    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']

    if req['session']['new']:
        res['response']['text'] = 'Привет! Я умею играть в виселицу и хочу сыграть с тобой! Но для начала ' \
                                  'надо познакомиться. Как тебя зовут?'
        sessionStorage[user_id] = {
            'first_name': None,
            'game_started': False,  # здесь информация о том, что пользователь начал игру. По умолчанию False
            'category': None,
            'guessed_words': []
        }
        return
    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        # если не нашли, то сообщаем пользователю что не расслышали.
        if first_name is None:
            res['response']['text'] = \
                'Не расслышала имя. Повтори, пожалуйста!'
        # если нашли, то приветствуем пользователя.
        # И спрашиваем какой город он хочет увидеть.
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response'][
                'text'] = 'Приятно познакомиться, ' + first_name.title() \
                          + '. Я - Алиса. Хочешь сыграть в "Виселицу"?'
            # получаем варианты buttons из ключей нашего словаря cities
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                },
                {
                    'title': 'Правила',
                    'hide': True
                }
            ]
    else:
        # У нас уже есть имя, и теперь мы ожидаем ответ на предложение сыграть.
        # В sessionStorage[user_id]['game_started'] хранится True или False в зависимости от того,
        # начал пользователь игру или нет.

        if not sessionStorage[user_id]['game_started']:
            if req['request']['original_utterance'].lower() in agree:
                if len(sessionStorage[user_id]['guessed_words']) > 83:
                    # если все три города отгаданы, то заканчиваем игру
                    res['response']['text'] = 'Ты отгадал все слова!'
                    res['end_session'] = True
                else:
                    res['response']['text'] = 'Выбери категорию, слово из которой ты хочешь угадать! Доступные темы:' \
                                              ' животные, растения, школьные термины, известные люди, информатика'

                    res['response']['buttons'] = [
                        {
                            'title': topic.title(),
                            'hide': True
                        } for topic in all_w
                    ]
                    return
            elif req['request']['original_utterance'].lower() == 'правила':
                res['response']['text'] = rules

                res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                },
                {
                    'title': 'Правила',
                    'hide': True
                }
                ]
            elif req['request']['original_utterance'].lower() in disagree:
                res['response']['text'] = 'Ну нет - так нет. Приходи потом!'

                sessionStorage[user_id]['game_started'] = False
                res['end_session'] = True
            elif req['request']['original_utterance'].lower() in all_w:
                res['response']['text'] = 'Выбери категорию сложности! Доступные:' \
                                        ' простой, средний, сложный'

                res['response']['buttons'] = [
                    {
                        'title': lvl.title(),
                         'hide': True
                    } for lvl in all_w[req['request']['original_utterance'].lower()]
                ]
                sessionStorage[user_id]['category'] = req['request']['original_utterance'].lower()
            elif sessionStorage[user_id]['category'] != None:
                if req['request']['original_utterance'].lower() in all_w[sessionStorage[user_id]['category']]:
                    random_word = random.choice\
                    (all_w[sessionStorage[user_id]['category']][req['request']['original_utterance'].lower()])
                    n = 0
                    while random_word in sessionStorage[user_id]['guessed_words'] and n < 20:
                        n += 1
                        random_word = random.choice(all_w[sessionStorage[user_id]['category']][req['request']['original_utterance'].lower()])
                    if n >= 20:
                        res['response']['text'] = 'Похоже, ты угадал все слова из этой категории. Продолжить?'
                        res['response']['buttons'] = [
                        {
                            'title': 'Да',
                            'hide': True
                        },
                        {
                            'title': 'Нет',
                            'hide': True
                        },
                        {
                            'title': 'Правила',
                            'hide': True
                        }
                        ]
                        return
                    sessionStorage[user_id]['word'] = random_word
                    sessionStorage[user_id]['attempt'] = 1
                    sessionStorage[user_id]['wrong'] = []
                    sessionStorage[user_id]['current_word'] = ''

                    if ' ' not in random_word:
                        sessionStorage[user_id]['current_word'] = '*' * len(random_word)
                    else:
                        for i in random_word:
                            if i == ' ':
                                sessionStorage[user_id]['current_word'] += ' '
                            else:
                                sessionStorage[user_id]['current_word'] += '*'

                    res['response']['text'] = 'Отлично! Твоя категория - {}.\
                    Твое слово состоит из {} букв. Сейчас слово выглядит так: {}. Введи букву'.format(
                    sessionStorage[user_id]['category'] + ', ' +  req['request']['original_utterance'].lower(),
                        len(random_word),  sessionStorage[user_id]['current_word'])

                    sessionStorage[user_id]['game_started'] = True
                    return
                else:
                    res['response']['text'] = 'Непонятный запрос, напиши ещё раз!'
            else:
                res['response']['text'] = 'Непонятный запрос, напиши ещё раз!'
        else:
            play_game(res, req)


def play_game(res, req):
    user_id = req['session']['user_id']
    word = sessionStorage[user_id]['word']
    attempt = sessionStorage[user_id]['attempt']
    cur_word = sessionStorage[user_id]['current_word']
    wrong = sessionStorage[user_id]['wrong']
    if '205039420' in req['request']['original_utterance']:
        res['response']['text'] = 'Осторожно! Секретная информация.\n Загаданное слово - {}\nПродолжить?'.format(word.title())
        res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                },
                {
                    'title': 'Правила',
                    'hide': True
                }
            ]
        return
    if 'виселиц' in req['request']['original_utterance'].lower():
        res['response']['text'] = 'Невозможно отобразить изображение :('
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = 'Виселица'
        res['response']['card']['description'] = 'Вот так сейчас выглядит виселица. Продолжить игру?'
        res['response']['card']['image_id'] = stages[len(wrong)]

        res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                },
                {
                    'title': 'Правила',
                'hide': True
                }
            ]
        return

    if req['request']['original_utterance'].lower() == 'правила':
        res['response']['text'] = rules

        res['response']['buttons'] = [
        {
            'title': 'Да',
            'hide': True
        },
        {
            'title': 'Нет',
            'hide': True
        },
        {
            'title': 'Правила',
            'hide': True
        }
        ]
        return
    if req['request']['original_utterance'].lower() in stop:
        res['response']['text'] = 'Ну нет - так нет. Приходи потом!'

        sessionStorage[user_id]['game_started'] = False
        res['end_session'] = True
        return
    if 'нет' in req['request']['original_utterance'].lower():
        res['response']['text'] = 'Ну нет - так нет. Приходи потом!'

        sessionStorage[user_id]['game_started'] = False
        res['end_session'] = True
        return
    if 'да' in req['request']['original_utterance'].lower():
        res['response']['text'] = 'Отлично! \nОшибки: {}\n' \
        'Слово: {} \nВведите следующую букву' .format(', '.join(wrong), cur_word)
        return
    if word not in req['request']['original_utterance'].lower():
        if attempt == 1:
            if re.search('[а-я]', req['request']['original_utterance'].lower()) \
                    and len(req['request']['original_utterance'].lower()) == 1:
                if req['request']['original_utterance'].lower() in word and req['request'][
                    'original_utterance'].lower() not in cur_word:
                    for i in range(len(word)):
                        if word[i] == req['request']['original_utterance'].lower():
                            if i + 1 != len(word):
                                cur_word = cur_word[:i] + word[i] + cur_word[i + 1:]
                            else:
                                cur_word = cur_word[:i] + word[i]

                    res['response']['text'] = 'Ого, с первой попытки!\n Ошибки: {}\n' \
                                              'Слово: {}.\nВведите следующую букву'.format(
                        ', '.join(wrong), cur_word)

                    sessionStorage[user_id]['attempt'] += 1
                    sessionStorage[user_id]['current_word'] = cur_word

                elif req['request']['original_utterance'].lower() in cur_word:
                    res['response']['text'] = 'Вы уже вводили такую букву. \nОшибки: {}\n' \
                                              'Слово: {}. \nВведите следующую букву' \
                        .format(', '.join(wrong), cur_word)

                else:
                    if req['request']['original_utterance'].lower() in wrong:

                        res['response']['text'] = 'Вы уже вводили такую букву. \nОшибки: {}\n' \
                                                  'Слово: {} \nВведите следующую букву' \
                            .format(', '.join(wrong), cur_word)

                    else:
                        wrong.append(req['request']['original_utterance'].lower())

                        sessionStorage[user_id]['wrong'] = wrong
                        sessionStorage[user_id]['attempt'] += 1

                        res['response']['text'] = 'Такой буквы нет в слове. \nОшибки: {}\n' \
                                                  'Слово: {}\nВведите следующую букву' \
                            .format(', '.join(wrong), cur_word)
            else:
                res['response']['text'] = 'Неверный символ! \nОшибки: {}\n' \
                                          'Слово: {}\nВведите следующую букву'.format(', '.join(wrong),
                                                                                                          cur_word)

        else:
            if cur_word != word:
                if re.search('[а-я]', req['request']['original_utterance'].lower()) \
                        and len(req['request']['original_utterance'].lower()) == 1:
                    if req['request']['original_utterance'].lower() in word and req['request'][
                        'original_utterance'].lower() not in cur_word:
                        for i in range(len(word)):
                            if word[i] == req['request']['original_utterance'].lower():
                                if i + 1 != len(word):

                                    cur_word = cur_word[:i] + word[i] + cur_word[i + 1:]
                                else:
                                    cur_word = cur_word[:i] + word[i]
                        res['response']['text'] = 'Такая буква действительно есть в слове!\nОшибки: {}\n' \
                                                  'Слово: {}.\nВведите следующую букву'.format(
                            ', '.join(wrong), cur_word)

                        sessionStorage[user_id]['attempt'] += 1
                        sessionStorage[user_id]['current_word'] = cur_word

                    elif req['request']['original_utterance'].lower() in cur_word:
                        res['response']['text'] = 'Вы уже вводили такую букву. \nОшибки: {}\n' \
                                                  'Слово: {}. \nВведите следующую букву' \
                            .format(', '.join(wrong), cur_word)

                    else:
                        if req['request']['original_utterance'].lower() in wrong:
                            res['response']['text'] = 'Вы уже вводили такую букву. \nОшибки: {}\n' \
                                                      'Слово: {} \nВведите следующую букву' \
                                .format(', '.join(wrong), cur_word)

                        else:
                            wrong.append(req['request']['original_utterance'].lower())

                            sessionStorage[user_id]['wrong'] = wrong
                            sessionStorage[user_id]['attempt'] += 1

                            res['response']['text'] = 'Такой буквы нет в слове. \nОшибки: {}\n' \
                                                      'Слово: {}\nВведите следующую букву' \
                                .format(', '.join(wrong), cur_word)
                else:
                    res['response']['text'] = 'Неверный символ! \nОшибки: {}\n' \
                                              'Слово: {}\nВведите следующую букву'.format(
                        ', '.join(wrong),
                        cur_word)
            if cur_word == word:
                sessionStorage[user_id]['guessed_words'].append(word)

                request = "https://ru.wikipedia.org/w/api.php"

                search_params = {
                    "action": "opensearch",
                    "search": word,
                    "format": "json"
                }

                response = requests.get(request, params=search_params)

                json_response = response.json()
                if json_response[2][0]:
                    info = json_response[2][0]

                    res['response']['tts'] = '<speaker audio="alice-sounds-game-win-2.opus">'

                    res['response']['text'] = 'Поздравляем, {}! Это победа. \nУгаданное слово - {}\nКстати! {}\nНачать новую игру?'\
                    .format(sessionStorage[user_id]['first_name'].title(), word.title(), info)

                    res['response']['buttons'] = [
                        {
                            'title': 'Да',
                            'hide': True
                        },
                        {
                            'title': 'Нет',
                            'hide': True
                        }
                    ]
                    sessionStorage[user_id]['game_started'] = False
                else:
                    res['response']['tts'] = '<speaker audio="alice-sounds-game-win-2.opus">'

                    res['response']['text'] = 'Поздравляем, {}! Это победа. \nУгаданное слово - {}\nНачать новую игру?'\
                    .format(sessionStorage[user_id]['first_name'].title(), word.title())

                    res['response']['buttons'] = [
                        {
                            'title': 'Да',
                            'hide': True
                        },
                        {
                            'title': 'Нет',
                            'hide': True
                        }
                    ]

                    sessionStorage[user_id]['game_started'] = False
    else:
        request = "https://ru.wikipedia.org/w/api.php"

        search_params = {
            "action": "opensearch",
            "search": word,
            "format": "json"
            }

        response = requests.get(request, params=search_params)
        sessionStorage[user_id]['guessed_words'].append(word)

        json_response = response.json()
        if json_response[2][0]:
            info = json_response[2][0]
            res['response']['tts'] = '<speaker audio="alice-sounds-game-win-2.opus">'

            res['response']['text'] = 'Поздравляем, {}! Это победа. \nУгаданное слово - {}\nКстати! {}\nНачать новую игру?'\
            .format(sessionStorage[user_id]['first_name'].title(), word.title(), info)

            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                },
                {
                    'title': 'Правила',
                    'hide': True
                }
            ]

            sessionStorage[user_id]['game_started'] = False
            return
        else:
            res['response']['tts'] = '<speaker audio="alice-sounds-game-win-2.opus">'

            res['response']['text'] = 'Поздравляем, {}! Это победа. \nУгаданное слово - {}\nНачать новую игру?'\
            .format(sessionStorage[user_id]['first_name'].title(), word.title())

            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                }
            ]

            sessionStorage[user_id]['game_started'] = False
            return
    if len(wrong) == 8:
        request = "https://ru.wikipedia.org/w/api.php"

        search_params = {
            "action": "opensearch",
            "search": word,
            "format": "json"
            }

        response = requests.get(request, params=search_params)

        json_response = response.json()

        if json_response[2][0]:
            info = json_response[2][0]

            res['response']['text'] = '{}, к сожалению, слово не отгадано. \nЗагаданное слово - {}\nКстати! {}\nПопробуете ещё раз?'\
            .format(sessionStorage[user_id]['first_name'].title(), word.title(), info)

            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                }
            ]

            sessionStorage[user_id]['game_started'] = False
            sessionStorage[user_id]['guessed_words'].append(word)
            return
        else:
            res['response']['text'] = '{}, к сожалению, слово не отгадано. \nЗагаданное слово - {}\nПопробуете ещё раз?'\
            .format(sessionStorage[user_id]['first_name'].title(), word.title())

            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                }
            ]

            sessionStorage[user_id]['game_started'] = False
            sessionStorage[user_id]['guessed_words'].append(word)


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name',
            # то возвращаем ее значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    app.run()
