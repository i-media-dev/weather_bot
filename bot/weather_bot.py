import logging

from dotenv import load_dotenv
from telebot import TeleBot

from bot.constants import (COLD_ROBOT, HOT_ROBOT, ICE_ROBOT, MAX_TEMPERATURE,
                           MIN_TEMPERATURE, ROBOTS_FOR_WEATHER,
                           TRIGGER_SUB_STRINGS)
from bot.logging_config import setup_logging
from pathlib import Path
from bot.yesterday_temperature import YESTERDAY_TEMP

load_dotenv()

setup_logging()


class WeatherAlertBot:

    def __init__(self, token: str, chat_id: str):
        self.chat_id = chat_id
        self.bot = TeleBot(token)

    def _make_file(self, filename: str) -> Path:
        """
        Защищенный метод, создает файл, если его нет.

        :param filename: название файла, который нужно создать.
        :type filename: str
        :return: возвращает путь к файлу.
        :rtype: Path
        """
        try:
            file_path = Path(__file__).parent / filename
            return file_path
        except Exception as error:
            logging.error('Не удалось создать файл по причине %s', error)
            raise

    def _save_temperature(self, temperature: float):
        """
        Защищенный метод, сохраняет температуру в файл.

        :param temperature: температура, полученная из API
        :type temperature: float
        """
        try:
            file_path = self._make_file('yesterday_temperature.py')
            file_content = f'YESTERDAY_TEMP = {temperature}\n'
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
            logging.info('Вчерашняя температура обновлена %s', temperature)
        except Exception as error:
            logging.error(
                'Неожиданная ошибка при сохранении температуры: %s',
                error
            )

    def get_robot(
        self,
        bot: TeleBot,
        robot: str,
        chat_id: str,
        robot_folder: str = 'robots'
    ) -> None:
        """
        Метод отправки стикера с роботом в бота.

        :param bot: Объект бота
        :type bot: TeleBot
        :param robot: Название файла с роботом
        :type robot: str
        :param chat_id: ID чата или группы для отправки сообщения
        :type chat_id: str
        :param robot_folder: Директория расположения файла
        с изображением робота.
        :type robot_folder: str
        """
        try:
            with open(f'{robot_folder}/{robot}', 'rb') as photo:
                bot.send_sticker(chat_id, photo)
        except FileNotFoundError:
            logging.warning('Робот %s не найден', robot)

    def send_message_str(
        self,
        bot: TeleBot,
        chat_id: str,
        message_str: str
    ) -> None:
        """
        Метод для отправки сообщений в бота.

        :param bot: Объект бота
        :type bot: TeleBot
        :param chat_id: ID чата или группы для отправки сообщения
        :type chat_id: str
        :param message_str: Текст сообщения
        :type message_str: str
        """
        try:
            bot.send_message(
                chat_id=chat_id,
                text=message_str,
            )
            logging.info('Сообщение отправлено получателю %s', chat_id)
        except Exception as error:
            logging.error('Ошибка при отправке сообщения: %s', error)
            raise

    def _message_constructor(self, weather: str, temperature: float) -> tuple:
        """
        Защищенный метод, составляет сообщение для
        бота на основе полученных данных из API.

        :param weather: Описание температуры по коду, полученному из API
        :type weather: str
        :param temperature: температура, полученная из API
        :type temperature: float
        :return: Возвращает строку с сообщением для бота
        и название файла с нужным роботом
        :rtype: tuple[str, str]
        """
        robot = ''
        message_parts = []
        weather_triggered = False

        for substring in TRIGGER_SUB_STRINGS:
            if substring in weather:
                robot = ROBOTS_FOR_WEATHER.get(weather, '')
                message_parts.append(f'Птичка напела, что на улице {weather}.')
                weather_triggered = True
                break

        if temperature < MIN_TEMPERATURE:
            temperature_message = (
                f'Мороз! Средняя температура воздуха {temperature}°C.'
            )
            if not weather_triggered:
                robot = COLD_ROBOT
        elif temperature > MAX_TEMPERATURE:
            temperature_message = (
                f'Жара! Средняя температура воздуха {temperature}°C.'
            )
            if not weather_triggered:
                robot = HOT_ROBOT
        else:
            temperature_message = (
                f'Средняя температура воздуха {temperature}°C.'
            )

        message_parts.append(temperature_message)

        if not weather_triggered and YESTERDAY_TEMP:
            if YESTERDAY_TEMP > 0 and temperature < 0:
                change_message = (
                    f'Наблюдаю резкое снижение температуры с '
                    f'{YESTERDAY_TEMP}°C до {temperature}°C. '
                    'Вероятен гололед! 🧊🧊🧊'
                )
                message_parts.append(change_message)
                robot = ICE_ROBOT

        message_parts.append(
            'Вероятно, сегодня люди воздержатся от выхода из дома. '
            'Ожидаем повышенный спрос на доставку!'
        )

        final_message = ' '.join(message_parts)

        return robot, final_message

    def bot_reaction(self, temperature: float | str, weather: str) -> None:
        """
        Метод присылает реакцию на погоду в телеграмм.

        :param temperature: температура, полученная из API
        :type temperature: float | str
        :param weather: Описание температуры по коду, полученному из API
        :type weather: str
        """
        final_message = ''
        robot = ''
        try:
            if isinstance(temperature, str) or weather == 'неизвестно':
                logging.info('Мне не удалось узнать погоду.')
                return
            robot, final_message = self._message_constructor(
                weather,
                temperature
            )
            self._save_temperature(temperature)
            if robot and final_message:
                self.get_robot(self.bot, robot, self.chat_id)
                self.send_message_str(self.bot, self.chat_id, final_message)
        except Exception as error:
            logging.error(
                'Неожиданная ошибка во время отправки сообщения: %s',
                error
            )
