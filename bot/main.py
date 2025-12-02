import os

from bot.weather_bot import WeatherAlertBot
from bot.weather_client import WeatherDataFetcher


def main():
    token = os.getenv('TOKEN_TELEGRAM')

    if not token:
        raise ValueError('Отсутствует токен в переменных окружения')

    chat_id = os.getenv('CHAT_ID')

    if not chat_id:
        raise ValueError('Отсутствует ID чата в переменных окружения')

    weather_client = WeatherDataFetcher()
    weather_bot = WeatherAlertBot(token, chat_id)

    temperature, weather = weather_client.get_weather()
    weather_bot.bot_reaction(temperature, weather)
    # weather_bot.bot_reaction(-30, 'слабая ледяная морось 🌧️❄️')


if __name__ == '__main__':
    main()
