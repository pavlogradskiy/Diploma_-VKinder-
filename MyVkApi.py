from vk_api.vk_api import VkApi

PARAMETERS_FOR_SEARCH = ['bdate', 'sex', 'relation', 'city']


class MyVkApi(VkApi):
    users_find_list = []
    already_seen_users = []

    def get_param_value(self, parameter, user_info):
        if parameter in user_info:
            if parameter != 0:
                if parameter == 'city':
                    self.city = user_info['city']['id']
                    return True
                elif parameter == 'sex':
                    self.sex = user_info['sex']
                    return True
                elif parameter == 'bdate':
                    bdate_list = user_info['bdate'].split('.')
                    if len(bdate_list) == 3:
                        self.bdate = int(bdate_list[2])
                        return True
                else:
                    self.relation = user_info['relation']
                    return True

    def get_user_info(self, id=552934290):
        self.missing_params = []
        self.id = id
        user_info = self.method(
            'users.get',
            {
                'user_ids': self.id,
                'fields': ','.join(PARAMETERS_FOR_SEARCH)
            }
        )
        user_info = user_info[0]
        self.name = user_info['first_name']
        for parameter in PARAMETERS_FOR_SEARCH:
            if not self.get_param_value(parameter, user_info):
                self.missing_params.append(parameter)

    def find_city_id(self, city: str) -> int:
        '''
        Идентификатор города пользователя
        :param city: str
        :return: int
        '''
        values = {
            'country_id': 1,
            'q': city,
            'count': 1
        }
        response = self.method('database.getCities', values=values)
        if response['items']:
            city_id = response['items'][0]['id']
            return city_id


    def find_people(self):
        values = {
            'city': self.city,
            'sex': 3 - self.sex,
            'birth_year': self.bdate,
            'status': self.relation,
            'has_photo': 1,  # только пользователи с фотографиями
            'count': 1000  # количество пользователей в ответе
        }
        users_list = self.method('users.search', values=values)
        MyVkApi.users_find_list = users_list['items']

    def get_likes_and_comments(self, photo) -> list:
        likes = str(photo['likes']['count'])
        comments = str(photo['likes']['count'])
        photo_list = [likes, comments, photo['id']]
        return photo_list

    def _get_album_photos_inf(self, id, album='profile') -> list:
        values = {
            "owner_id": id,
            "access_token": self.token,
            "album_id": album,
            "extended": 1,
            "v": "5.131"
        }
        response = self.method('photos.get', values=values)
        return response['items']

    def get_top_photos(self, user_id=254731751) -> list:
        unsorted_photos = []
        photos_inf = self._get_album_photos_inf(user_id)  #id пользователя из поиска
        for photo in photos_inf:
            photo_list_for_sorted = self.get_likes_and_comments(photo)
            unsorted_photos.append(photo_list_for_sorted)
        sorted_photos = sorted(unsorted_photos, reverse=True)
        if len(sorted_photos) > 3:
            sorted_photos = sorted_photos[:3]
        photo_str = f'photo{user_id}_'
        top_photos = [f'{photo_str}{photo[2]}' for photo in sorted_photos]
        return top_photos

    def check_user(self, user):
        '''
        True - если пользователя нет в списке просмотренных, и его страница открыта
        '''
        if user['id'] not in MyVkApi.already_seen_users:
            if not user['is_closed']:
                return True
            else:
                MyVkApi.already_seen_users.append(user['id'])

    def get_users_info(self) -> list:
        self.find_people()
        if MyVkApi.users_find_list:
            users_info_for_print = []
            for user in MyVkApi.users_find_list:
                if len(users_info_for_print) == 3:
                    break
                if not self.check_user(user):
                    continue
                user_name = f"{user['first_name']} {user['last_name']}"
                user_id = user['id']
                user_url = 'https://vk.com/id' + str(user_id)
                user_photos = self.get_top_photos(user_id)
                user_info_dict = dict(
                    id=user_id,
                    name=user_name,
                    url=user_url,
                    photos=user_photos

                )
                users_info_for_print.append(user_info_dict)
                MyVkApi.already_seen_users.append(user_id)
            return users_info_for_print