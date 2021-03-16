import json 
import requests

from django.conf import settings
from django.http import JsonResponse

from sw_model_search import model_search

from .settings import NOVA_POSHTA_API_KEY
from .models import *



def handle_np(query={}, action='refresh', content='warehouses', type='from_json'):
    limit       = query.get('limit', 150)
    page        = query.get('page', 1)
    pages_limit = query.get('pages_limit', None)

    if content == 'warehouses':
        method   = 'getWarehouses'
        model    = "AddressGeneral"
        message  = 'Warehouses were successfully refreshed'
        filename = 'warehouses.json'
        func     = create_warehouses
    elif content == 'settlements':
        method   = 'getSettlements'
        model    = "AddressGeneral"
        message  = 'Settlements were successfully refreshed'
        filename = 'settlements.json'
        func     = create_settlements
    if action == 'refresh':
        print('refresh')
        if type == 'gen_json':
            response = get_full_response(model, method,
                limit=limit,
                page=page,
                pages_limit=pages_limit,
            )
            with open(filename, 'w') as f:
                f.write(json.dumps(response, indent=4))
        elif type == 'from_api':
            response = get_full_response(model, method,
                limit=limit,
                page=page,
                pages_limit=pages_limit,
            )
            func(response)
        elif type == 'from_json':
            with open(filename, 'r') as f:
                func(json.load(f))
        return JsonResponse({
            "message":message,
            "status": "OK",
        })
    elif action == 'browse':
        response = get_response(model, method,
            limit=limit,
            page=page,
        )
        return JsonResponse(response)




def get_response(modelName, calledMethod, limit=150, page=1):
    api_domain = 'https://api.novaposhta.ua'
    api_path = f'/v2.0/json/{modelName}/{calledMethod}'
    api_data = {
        'modelName': f'{modelName}',
        'calledMethod': f'{calledMethod}',
        'apiKey': NOVA_POSHTA_API_KEY,
        "methodProperties": {
            "Limit":limit,
            "Page":page,
        },
    }
    response = requests.post(api_domain + api_path, json=api_data).json()
    if not response.get('success'):
        raise Exception(','.join(response.get('errors')))
    return response 


def get_full_response(modelName, calledMethod, limit=150, page=1, pages_limit=None):
    response = {
        'data':[]
    } 
    while True:
        page_response = get_response(modelName, calledMethod, limit, page)
        data = page_response['data']
        if not data or pages_limit == page:
            break 
        for obj in data:
            response['data'].append(obj)
        page +=1
        print(page)
    return response 


def create_warehouses(response):
    Warehouse.objects.all().delete()
    warehouses = []
    data = response.get('data')
    for index, item in enumerate(data):
        print(f'{index} of {len(data)}')
        params = {
            'title': item.get('Description'),
            'address': item.get('CityDescription')
        }
        langs = dict(settings.LANGUAGES)
        if 'uk' in langs:
            params.update({
                'title_uk': item.get('Description'),
                'address_uk': item.get('CityDescription')
            })
        if 'ru' in langs:
            params.update({
                'title_ru': item.get('DescriptionRu'),
                'address_ru': item.get('CityDescriptionRu')
            })
        warehouses.append(Warehouse(**params))
    Warehouse.objects.bulk_create(warehouses)



def create_settlements(response):
    Settlement.objects.all().delete()
    Area.objects.all().delete()
    Region.objects.all().delete()
    Type.objects.all().delete()
    data = response['data']
    for index, item in enumerate(data):
        print(f'{index} of {len(data)}')
        # print(item)
        # print('index:', response['data'].index(item))
        # print()
        # print()
        latitude  = item.get('Latitude')
        longitude = item.get('Longitude')
        title     = item.get('Description')
        title_uk  = item.get('Description')
        title_ru  = item.get('DescriptionRu')
        type      = item.get("SettlementTypeDescription")
        type_uk   = item.get("SettlementTypeDescription")
        type_ru   = item.get("SettlementTypeDescriptionRu")
        region    = item.get('RegionsDescription')
        region_uk = item.get('RegionsDescription')
        region_ru = item.get('RegionsDescriptionRu')
        area      = item.get('AreaDescription')
        area_uk   = item.get('AreaDescription')
        area_ru   = item.get('AreaDescriptionRu')


        langs = dict(settings.LANGUAGES)
        type,_ = Type.objects.get_or_create(
            title      = type,
            title_uk   = type_uk,
        )
        area,_ = Area.objects.get_or_create(
            title    = area,
            title_uk = area_uk,
        )
        region,_ = Region.objects.get_or_create(
            title    = region,
            title_uk = region_uk,
            area      = area,
        )
        settlement, _ = Settlement.objects.get_or_create(
            latitude  = latitude,
            longitude = longitude,
            title     = title,
            title_uk  = title_uk,
            type      = type,
            region    = region,
        )
        if 'ru' in langs:
            type.title_ru       = title_ru
            area.title_ru       = title_ru
            region.title_ru     = title_ru
            settlement.title_ru = title_ru
            type.save()
            area.save()
            region.save()
            settlement.save()















