from bs4 import BeautifulSoup

class API:
    def process_response(self, response):
        return response.json()

class BS4:
    def process_response(self, response):
        return BeautifulSoup(response.content, 'html.parser')


class SELENIUM:
    pass

