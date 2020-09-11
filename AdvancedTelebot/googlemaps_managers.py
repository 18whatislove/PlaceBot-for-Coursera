import googlemaps
from storage import get_places_names
from googlemaps.places import places_nearby
from googlemaps.exceptions import TransportError


def check_place_id(variants, place_id):
    ids = filter(lambda variant: variant['place_id'] == place_id, variants['results'])
    return ids


def get_nearby_place(client, current_location, chat_id):
    result = {'message': 'Места в радиусе 500 метров', 'places': []}
    names = get_places_names(chat_id)
    if names:
        for name in names:
            try:
                selection = places_nearby(client, current_location, radius=500, name=name[1])
                if selection['results']:
                    result['places'] += check_place_id(selection, name[0])
                else:
                    continue
            except TransportError:
                result['message'] = 'Googlemaps временно не работает\nПовторите попытку позже'
        if not result['places']:
            result['message'] = 'Поблизости нет сохранённых мест.'
    else:
        result['message'] = 'Ваш список мест пуст!'
    return result


def get_place_info(client, current_location, keyword):  # Для установления точного адреса места, которое хотят сохранить
    try:
        selection = places_nearby(client, current_location, radius=200, name=keyword)
    except TransportError:
        return {'message': 'Googlemaps временно не работает\nПовторите попытку позже', 'place_info': {}}
    if selection['results']:
        places = selection['results']
        print(places)
        place = places[0]  # Чаще всего первый пример из выборки совпадает с местом пользователя
        location = place['geometry']['location']
        return {'message': 'OK!',
                'place_info': {'place_id': place['place_id'],
                               'name': place['name'],
                               'address': place['vicinity'],
                               'lat': location['lat'],
                               'lng': location['lng'],
                               'photo_id': None,
                               'visitor_id': None
                               }
                }
    else:
        return {'message': 'Информация о месте не найдена!', 'place_info': {}}
