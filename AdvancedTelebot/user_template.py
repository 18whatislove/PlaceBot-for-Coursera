class User():
    """Класс отвечаюсь за работу с пользователем и его данными"""
    lobby, stage1, stage2, stage3, confirmation = 'lobby', 'save_name', 'save_location', 'save_photo', 'confirmation'

    def __init__(self, id=None):
        self.id = id
        self.stage = self.lobby
        self.keyword = None  # Ключевое слово(название места) для поиска данных в googlemaps
        self.query = {'place_id': str,
                      'name': str,
                      'address': str,
                      'lat': float,
                      'lng': float,
                      'photo_id': str,
                      'visitor_id': int}

    def get_stage(self):
        return self.stage

    def set_stage(self, stage):
        self.stage = stage

    def show_query(self):
        return self.query

    def filling_query(self, data):
        data['visitor_id'] = self.id
        self.query = data

    def attaching_photo_id(self, photo):  # Сохраняет айди фото, чтобы потом с помощью него выводить пользователю
        self.query['photo_id'] = photo[0].file_id

    def send_query(self):
        return tuple([data for data in self.query.values()])





