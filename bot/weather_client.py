import logging

import requests
from dotenv import load_dotenv

from bot.constants import API_WEATHER_URL, PARAMS, TIMEOUT, WEATHER_CODE
from bot.logging_config import setup_logging

load_dotenv()

setup_logging()


class WeatherDataFetcher:

    def __init__(self):
        self.yesterday_temp = float()

    def _get_data_weather(self) -> dict:
        """
        Защищенный метод, делает запрос к API погоды
        и возвращает данные в виде json.

        Returns:
            dict: данные о погоде в формате json
        """
        try:
            response = requests.get(
                url=API_WEATHER_URL,
                params=PARAMS,
                timeout=TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logging.error('Таймаут подключения к API погоды')
            raise
        except requests.exceptions.HTTPError as error:
            logging.error('HTTP ошибка %s', error.response.status_code)
            raise
        except requests.exceptions.RequestException as error:
            logging.error('Ошибка запроса: %s', error)
            raise
        except Exception as error:
            logging.error(
                'Неожиданная ошибка запроса к API: %s',
                error,
                exc_info=True
            )
            raise

    def _parse_weather(self, data: dict) -> tuple:
        """
        Защищенный метод, парсит входящий json.

        Args:
            data (dict): ответ API в формате json

        Returns:
            tuple: максимальная температура (float),
            минимальная температура (float), погодный код (int)
        """
        try:
            weather = data['daily']
            max_temp = float(weather['temperature_2m_max'][0])
            logging.info('Получена максимальная температура  %s', max_temp)
            min_temp = float(weather['temperature_2m_min'][0])
            logging.info('Получена минимальная температура  %s', min_temp)
            weather_code = int(weather['weather_code'][0])
            logging.info('Получен погодный код - %s', weather_code)
            return max_temp, min_temp, weather_code
        except (KeyError, IndexError, TypeError, ValueError) as error:
            logging.error(
                'Некорректная структура данных: %s',
                error
            )
            raise
        except Exception as error:
            logging.error('Неожиданная ошибка парсинга: %s', error)
            raise

    def get_weather(
        self,
        default_temp: str = 'неизвестно',
        default_weather: str = 'неизвестно'
    ) -> tuple:
        """
        Метод возвращает валидные обработанные данные о погоде.
        Вычисляет среднюю температуру.
        Преобарзует погодный код в человекочитаемую характеристику погоды.

        Returns:
            tuple: средняя температура, тип погоды
        """
        try:
            data = self._get_data_weather()
            max_temp, min_temp, weather_code = self._parse_weather(data)
            avg_temp = round((max_temp + min_temp) / 2, 1)
            weather_type = WEATHER_CODE.get(weather_code, 'неизвестно')
            return avg_temp, weather_type
        except Exception as error:
            logging.error('Неожиданная ошибка: %s', error, exc_info=True)
            return default_temp, default_weather
