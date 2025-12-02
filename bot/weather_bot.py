import logging

from dotenv import load_dotenv
from telebot import TeleBot

from bot.constants import (COLD_ROBOT, HOT_ROBOT, ICE_ROBOT, MAX_TEMPERATURE,
                           MIN_TEMPERATURE, ROBOTS_FOR_WEATHER,
                           TRIGGER_SUB_STRINGS)
from bot.logging_config import setup_logging

load_dotenv()

setup_logging()


class WeatherAlertBot:

    def __init__(self, token: str, chat_id: str):
        self.chat_id = chat_id
        self.yesterday_temp = float()
        self.bot = TeleBot(token)

    def get_robot(
        self,
        bot: TeleBot,
        robot: str,
        chat_id: str,
        robot_folder: str = 'robots'
    ) -> None:
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

        if not weather_triggered and self.yesterday_temp:
            if self.yesterday_temp > 0 and temperature < 0:
                change_msg = (
                    f'Наблюдаю резкое снижение температуры с '
                    f'{self.yesterday_temp}°C до {temperature}°C. '
                    'Вероятен гололед! 🧊🧊🧊'
                )
                message_parts.append(change_msg)
                robot = ICE_ROBOT

        message_parts.append(
            'Вероятно, сегодня люди воздержатся от выхода из дома. '
            'Ожидаем повышенный спрос на доставку!'
        )

        final_message = ' '.join(message_parts)

        return robot, final_message

    def bot_reaction(self, temperature: float | str, weather: str) -> None:
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
            if robot and final_message:
                self.get_robot(self.bot, robot, self.chat_id)
                self.send_message_str(self.bot, self.chat_id, final_message)
        except Exception as error:
            logging.error(
                'Неожиданная ошибка во время отправки сообщения: %s',
                error
            )
