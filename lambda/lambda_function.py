import os
import json
import boto3
import requests

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])
API_KEY = os.environ["API_KEY"]

def get_european_capitals():
    url = "https://restcountries.com/v3.1/region/europe"
    response = requests.get(url)
    countries = response.json()
    capitals = []
    for country in countries:
        if 'capital' in country and 'capitalInfo' in country and 'latlng' in country['capitalInfo']:
            capitals.append({
                "country": country["name"]["common"],
                "capital": country["capital"][0],
                "lat": country["capitalInfo"]["latlng"][0],
                "lon": country["capitalInfo"]["latlng"][1]
            })
    return capitals

def get_air_pollution(lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erreur API pour coordonnées {lat},{lon} : {response.status_code}")
        return None

def lambda_handler(event, context):
    capitals = get_european_capitals()
    for city in capitals:
        pollution_data = get_air_pollution(city['lat'], city['lon'])
        if pollution_data and 'list' in pollution_data and pollution_data['list']:
            components = pollution_data['list'][0]['components']
            aqi = pollution_data['list'][0]['main']['aqi']
            item = {
                "city": city['capital'],
                "country": city['country'],
                "lat": str(city['lat']),
                "lon": str(city['lon']),
                "no": str(components.get('no', '')),
                "no2": str(components.get('no2', '')),
                "co": str(components.get('co', '')),
                "o3": str(components.get('o3', '')),
                "so2": str(components.get('so2', '')),
                "pm2_5": str(components.get('pm2_5', '')),
                "pm10": str(components.get('pm10', '')),
                "nh3": str(components.get('nh3', '')),
                "aqi": str(aqi)
            }
            table.put_item(Item=item)

    return {
        'statusCode': 200,
        'body': json.dumps('Données pollution insérées dans DynamoDB')
    }
