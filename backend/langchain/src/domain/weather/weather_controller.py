import logging

class WeatherController:
    def __init__(self, weather_service):
        self.weather_service = weather_service
        logging.info('WeatherController initialized')