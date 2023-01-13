from random import randrange

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard

import DbVk
from MyVkApi import MyVkApi


TOKEN_GROUP = ''
TOKEN_USER = ''
RELATION_DICT = {
    '1': 'не женат/не замужем',
    '2': 'есть друг/есть подруга',
    '3': 'помолвлен/помолвлена',
    '4': 'женат/замужем',
    '5': 'всё сложно',
    '6': 'в активном поиске',
    '7': 'влюблён/влюблена',
    '8': 'в гражданском браке'
}
PARAMETERS_FOR_SEARCH = ['bdate', 'sex', 'relation', 'city']

vk_bot = vk_api.VkApi(token=TOKEN_GROUP)
longpoll = VkLongPoll(vk_bot, wait=25)


def wait_new_message():
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            return event.text.lower()


def one_time_keyboard(buttons: list):
    new_keyboard = VkKeyboard(one_time=True)
    for button in buttons:
        new_keyboard.add_button(
            label=button,
            color='primary'
        )
        if button != buttons[-1]:
            new_keyboard.add_line()
    return new_keyboard


def all_time_keyboard(buttons: list):
    new_keyboard = VkKeyboard(one_time=False)
    for button in buttons:
        new_keyboard.add_button(
            label=button,
            color='primary'
        )
        if button != buttons[-1]:
            new_keyboard.add_line()
    return new_keyboard


def write_msg(user_id, message, keyboard=None, attachment=None):
    vk_bot.method(
        'messages.send',
              {
                  'user_id': user_id,
                  'message': message,
                  'random_id': randrange(10 ** 7),
                  'keyboard': keyboard,
                  'attachment': attachment
              }
    )


def send_goodbye_msg(vk_user):
    write_msg(
        user_id=vk_user.id,
        message="Пока((",
        keyboard=all_time_keyboard(['Начать']).get_keyboard()
    )


def ask_params(missing_params, vk_user):
    for param in missing_params:
        while True:
            if param == 'bdate':
                write_msg(vk_user.id, 'Год рождения?\n(YYYY)')
                bdate = wait_new_message()
                if bdate.lower() == 'пока':
                    return True
                if bdate.isdigit() and 1930 <= int(bdate) <= 2006:
                    vk_user.bdate = bdate
                    break
            elif param == 'sex':
                write_msg(vk_user.id, 'Ваш пол:\n1 - женский\n2 - мужской')
                sex = wait_new_message()
                if sex.lower() == 'пока':
                    return True
                if sex == '1' or sex == '2':
                    vk_user.sex = int(sex)
                    break
            elif param == 'relation':
                message = 'В каких вы отношениях?\n'
                for indx, name in RELATION_DICT.items():
                    message += f'{indx} - {name}\n'
                write_msg(vk_user.id, message)
                relation = wait_new_message()
                if relation.lower() == 'пока':
                    return True
                if relation in RELATION_DICT:
                    vk_user.relation = int(relation)
                    break
            else:
                write_msg(vk_user.id, 'Из какого вы города?')
                city = wait_new_message()
                if city.lower() == 'пока':
                    return True
                if city.isalpha():
                    city_id = vk_user.find_city_id(city)
                    if city_id:
                        vk_user.city = city_id
                        break
            write_msg(vk_user.id, 'Некорректный ввод')


def show_three_users(vk_user, session):
    new_users = vk_user.get_users_info()
    if new_users:
        for user in new_users:
            DbVk.add_found_user(session, vk_user.id, user)
            message = f'{user["name"]}\n{user["url"]}'
            attachment = ','.join(user["photos"])
            write_msg(user_id=vk_user.id, message=message, attachment=attachment)
    else:
        buttons = [
            'Задать новые параметры',
            'На сегодня хватит'
        ]
        write_msg(
            user_id=vk_user.id,
            message='Пользователи не найдены.',
            keyboard=one_time_keyboard(buttons).get_keyboard()
        )


def start_bot(session):

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            text_message = event.text.lower()
            sender_id = event.user_id

            if text_message in ('начать', 'привет', 'салют', 'хай', 'ghbdtn', 'start'):
                DbVk.add_user_session(session=session, sender_id=sender_id)
                vk_user = MyVkApi(token=TOKEN_USER)
                vk_user.get_user_info(sender_id)
                message = f'Салют, {vk_user.name}\n' \
                         f'Ты здесь, чтобы найти себе пару. И я помогу.\n' \
                          f'Не забудь написать мне "пока" или нажать ' \
                          f'кнопку "на сегодня хватит", ' \
                          f'чтобы сохранить результаты поиска'
                buttons = ['Поиск по текущим параметрам', 'Задать новые параметры']
                write_msg(
                    user_id=vk_user.id,
                    message=message,
                    keyboard=one_time_keyboard(buttons).get_keyboard()
                )

            elif text_message in ('поиск по текущим параметрам', 'задать новые параметры'):
                bye_bye = None
                if vk_user:
                    if text_message == 'задать новые параметры':
                        bye_bye = ask_params(PARAMETERS_FOR_SEARCH, vk_user)
                    elif text_message == 'поиск по текущим параметрам' and vk_user.missing_params:
                        write_msg(vk_user.id, 'Мне нужно еще немного информации о вас.')
                        bye_bye = ask_params(vk_user.missing_params, vk_user)

                    if bye_bye:
                        send_goodbye_msg(vk_user)
                    else:
                        buttons = [
                            'Показать еще 3х человек',
                            'Задать новые параметры',
                            'На сегодня хватит'
                        ]
                        write_msg(
                            user_id=vk_user.id,
                            message='А теперь приступим к поиску.',
                            keyboard=all_time_keyboard(buttons).get_keyboard()
                        )
                        show_three_users(vk_user, session)

            elif text_message == 'показать еще 3х человек':
                show_three_users(vk_user, session)

            elif text_message in ('пока', 'на сегодня хватит'):
              send_goodbye_msg(vk_user)
              break
            else:
                write_msg(vk_user.id, "Не понял вашего ответа...")

if __name__ == '__main__':
    print('Start')
    DbVk.Base.metadata.create_all(DbVk.engine)
    session = DbVk.Session()
    start_bot(session)
    session.commit()
    print('Finish')