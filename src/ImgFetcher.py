'''
Created on Apr 2, 2018

@author: Robin
'''

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


def img_fetcher(PATH, url_link, query="", load_limit=5):
    # format the query for search, in case of multiple words
    query.lower().replace(" ", "%20")

    # generate the query link
    url = url_link.format(query)

    # config chrome driver option
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--test-type")
    options.add_argument('headless')

    # create chrome driver
    try:
        driver = webdriver.Chrome(executable_path=PATH, chrome_options=options)
    except Exception:
        pass
    # visit url
    driver.get(url)
    # wait for the site to load, let js generate html
    delay = 5
    try:
        WebDriverWait(driver, delay).until(
            EC.presence_of_element_located((By.TAG_NAME, 'figure')))

        print("Finished loading image site")
    except TimeoutException:
        print("Image site loading timeout")
    # get the image element
    images = driver.find_elements_by_css_selector('figure img')

    # add the image link to the result list
    result = [image.get_attribute('data-src') for image in images[:load_limit]]
    # close driver  and return
    driver.close()
    return result
