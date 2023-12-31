
CrawlFlow

This module is a tool for web scrap handling. 

How to use:
Importing packages
```python
from CrawlFlow.handler import Handler
from CrawlFlow import types as CrawlTypes
```

Crawl types
if you are getting an API request
```python
self.type=CrawlTypes.API()
```
and if you are getting an HTML request and using BS4
```python
self.type=CrawlTypes.BS4()
```

Defining the crawler class
```python
class TestCrawler(Handler):
    def __init__(self, name):
        super().__init__(name)
        self.type=CrawlTypes.API()

    def data2rows(self, request_data):
        '''you scrap code here'''

        tables_rows={'videoList': videoList}
        
        return tables_rows
```
You need to define a method in the class called "data2rows". 
in this function you will get a variable called "request_data" that is your desired data (in API, json data/ in BS4, BS4 object)

Output of this function must be a python dictionary in this format:
```
tables_rows={'table1': table1,
'table2': table2, ...}
```
tables are list of dicts like below:
```
[ {'col1': 'col1_data', 'col2': 'col2_data'},
{'col1': 'col1_data', 'col2': 'col2_data'},
...]
```

Now we use our scrap class
```python
  scraper=TestCrawler('name of your scrap query')
  scraper.request.sleep_time=1.5
  scraper.chk_point_interval=20
  scraper.init()
  url_list=['list of URLs that you want to scrap']
  scraper.run(url_list, resume=False, dynamic=False)
  scraper.export_tables()
```


Setting Headers, Cookies and Params
```python
#setting manullay:
Handler.request.headers=Headers
Handler.request.cookies=Cookies
Handler.request.params=Params

#Or you can read from json file
Handler.request.read_headers(headers_path)
Handler.request.read_cookies(cookies_path)

```

Handler.chk_point_interval
```
Request interval for checkpoint data
```

Handler.directory
```
Director for saving the data
```

Hanlder.run(url_list, resume=False, dynamic=False)
```
url_list: List ==> list of URLs

resume: False==> new start / True==> continue from last checkpoint

dynamic: False==> standard scraping due to url_list / True==> for cases that have next url keys
```
----------------------------
Dynamic Scraping:

By setting dynamic = True in Hanlder.run method, you can use dynamic scraping

"url_list" should contian first url that starts scrping

```python
class TestCrawler(Handler):
    def __init__(self, name):
        super().__init__(name)
        self.type=CrawlTypes.API()
 
    def data2rows(self, request_data):
        self.data=request_data
        if request_data['data'][0]['link'] is  None:
            self.vars.done=True
            return {}
        self.vars.next_url = f'https://www.aparat.com/api/fa/v1/video/video/search/text/'+self.get(request_data['data'][0], ['link', 'next']).split('text/')[1]
        
        videoList=self.get(request_data['data'][0], ['video', 'data']) 
        tables_rows={'videoList': videoList}
        return tables_rows


crawler=TestCrawler('aparat')
crawler.request.params={'type_search': 'search'}
crawler.init()
url_list=['https://www.aparat.com/api/fa/v1/video/video/search/text/game']
crawler.run(url_list, resume=False, dynamic=True)
crawler.export_tables()

```
Note:
Hanlder.vars is an object that will be save in every ckeckpoint. so you set your variables here

```
If you set Hanlder.vars.done=True scraping process will be finished after that.
```

Defining response status codes for interrupting the process
```
Handler.request.bypass_status_codes = [204]
#If status codes be 204 request_data in data2rows will be like this:
{'status_code': 204}
```

-----------------------------
Sending to databases

first you should set Handler.DB_type to sqllite/mongo/local befor Handler.init()
**sqllite**: It is default value and will send data to the local sqllite database

**mongo**: It will send data to data MongoDB. also you need to set Handler.DB_info
```python
Handler.DB_info = {'database': 'myDataBase',
                    'connetion_string': 'MongoDB connetion_string'
                    }
```

**local**: It will save data in pickle object. note that this option is for small size data.

-----------------------------




