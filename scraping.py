from selenium import webdriver 
from selenium.webdriver.common.by import By 
from selenium.webdriver.chrome.service import Service as ChromeService 
from webdriver_manager.chrome import ChromeDriverManager 
import time 
from bs4 import BeautifulSoup
import csv
from zenrows import ZenRowsClient

#  f04c713777a1fcef35fd213ca35313e580a5d048
client = ZenRowsClient("f04c713777a1fcef35fd213ca35313e580a5d048")

options = webdriver.ChromeOptions() 
options.headless = True 
driver = webdriver.Chrome(service=ChromeService( 
	ChromeDriverManager().install()), options=options) 
 
# load target website 
url = 'https://www.zillow.com/ca/fsbo/' 
 
# get website content 
driver.get(url) 

# instantiate height of webpage 
last_height = driver.execute_script('return document.body.scrollHeight') 
 
def scroll_down():
    # Scroll down 100 pixels
    driver.execute_script("window.scrollBy(0, 100);")
    
if __name__ == '__main__':
    result = []
    page_number = 0
    page_content=''
    # Scroll down every 0.5 seconds
    while True:
        current_scroll_position = driver.execute_script("return window.pageYOffset;") 
    
        if current_scroll_position >= last_height-1500: 
            page_content = driver.page_source
            driver.quit()
            break

        scroll_down()
        time.sleep(0.2)
        
    soup = BeautifulSoup(page_content, 'html.parser')
    page_number = int(soup.find('span', class_="result-count").text.split(' ')[0])
    divs = soup.find_all('div', class_='property-card-data')
    links = list()
    for div_element in divs:
        liElements = div_element.find('ul', class_='StyledPropertyCardHomeDetailsList-c11n-8-84-3__sc-1xvdaej-0 eYPFID').find_all('li')
        if len(liElements) < 3:
            continue
        links.append({'link':div_element.find('a').get('href'), 
                      'bds':liElements[0].find('b').text,
                      'ba': liElements[1].find('b').text,
                      'sqft': liElements[2].find('b').text})
    # print(links)
    i =0
    for element in links:
        i +=1
        # if i ==3:
        #     break
        link = element['link']
        # driver = webdriver.Chrome(service=ChromeService( 
	    #     ChromeDriverManager().install()), options=options) 
        # driver.get(link)
        # page_content = driver.page_source
        # driver.quit()
        params = {
            "js_render": "true",
            "wait": 2000
        }
        while True:
            response = client.get(link, params=params)
            print(response.status_code, link)
            if response.status_code ==200:
                page_content = response.text
                break
        soup = BeautifulSoup(page_content, 'html.parser')
        item = {}
        item['price'] = soup.find('span', class_='Price__StyledHeading-sc-1me8eh6-0').text
        item['address'] = soup.find('h1', class_= 'Text-c11n-8-84-3__sc-aiai24-0').text.replace(',', '').replace('\xa0', '')
        # tmpValues = soup.find('ul', class_ = 'AtAGlanceFacts__StyledAtAGlanceFacts-sc-xzpkxd-0 fqMXPj').find_all('li')
        # # item['ba'] = soup.find('span', {'data-testid': 'bed-bath-item'} ).find('strong').text
        item['bds'] = element['bds']
        item['ba'] = element['ba']
        item['sqft'] = element['sqft']
        
        liElements = soup.find('ul', class_="AtAGlanceFacts__StyledAtAGlanceFacts-sc-xzpkxd-0 fqMXPj").find_all('li')
        item['type'] = ''
        item['lot'] = ''
        item['yearbuilt'] = ''
        
        for liElement in liElements:
            text = liElement.find('title').text
            if text == 'Type':
                item['type'] = liElement.find('span', class_='Text-c11n-8-84-3__sc-aiai24-0 AtAGlanceFact__StyledfactValue-sc-2arhs5-3 hrfydd iYUreA').text
            if text == 'Year Built':
                item['yearbuilt'] = liElement.find('span', class_='Text-c11n-8-84-3__sc-aiai24-0 AtAGlanceFact__StyledfactValue-sc-2arhs5-3 hrfydd iYUreA').text.split(' ')[2]
            if text == 'Lot':
                item['lot'] = liElement.find('span', class_='Text-c11n-8-84-3__sc-aiai24-0 AtAGlanceFact__StyledfactValue-sc-2arhs5-3 hrfydd iYUreA').text.split(' ')[0].replace(',', '')                                                      
                                                    #   Text-c11n-8-84-3__sc-aiai24-0 sc-laZRCg hrfydd
        item['overview'] = soup.find('div', class_ = 'sc-laZRCg').text
        dtElements = soup.find('dl', class_ = 'OverviewStatsComponents__StyledOverviewStats-sc-7d6bsa-0').find_all('dt')
        item['days'] = dtElements[0].find('strong').text.split(' ')[0]
        item['phone'] = soup.find('p', {'data-testid': 'attribution-PROPERTY_OWNER'}).find('span').text
        item['link'] = link
        
        result.append(item)        

    field_names = ['address', 'bds', 'ba', 'price', 'sqft', 'type', 'lot', 'yearbuilt', 'days', 'overview', 'phone', 'link']
        
    with open('result.csv', 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=field_names)

        # Write the header row
        writer.writeheader()

        # Write each object as a row in the CSV file
        writer.writerows(result)