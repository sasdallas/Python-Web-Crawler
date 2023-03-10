# Python web crawler - written by sasdallas
# The code is trash so don't use it but please give credit if you do

import requests
from bs4 import BeautifulSoup
import mechanize
import time
from http import cookiejar

baseURL = input("[?] What is the base URL? ")

urls = []
authURLs = []

# ugly but it works
ignoreWeirdSlashTricks = True
askedUserAboutPreferences = False


# https://stackoverflow.com/questions/1883980/find-the-nth-occurrence-of-substring-in-a-string
def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start

def crawlHTML(content):
    global urls
    global ignoreWeirdSlashTricks
    global askedUserAboutPreferences
    soup = BeautifulSoup(content, "html.parser")
    for link in soup.find_all("a"):
        if link.get("href") != "#" and link.get("href") not in urls and "http" not in link.get("href"):
            # Some pages use this trick where they basically use part of the URL as parameters, like Django.
            # Example: /likecomment/This%20is%20cool is a URL. Iterate thorugh all URLS 

            badURL = False
            if not askedUserAboutPreferences:
                if find_nth(link.get("href"), "/", 2) != -1:
                    print("An odd URL was encountered. It has been flagged as a possible 'parameter url' or whatever it's called.")
                    print("URL: " + link.get("href"))
                    a = input("Do you want to ignore all URLs like this from now on (specify 'o' for one time') ? [y/n/o] ")
                    if a == "n":
                        ignoreWeirdSlashTricks = False
                        askedUserAboutPreferences = True
                    elif a == "o":
                        badURL = True
                            
                    else:
                        ignoreWeirdSlashTricks = True
                        askedUserAboutPreferences = True
                
            
            if ignoreWeirdSlashTricks and askedUserAboutPreferences:
                if find_nth(link.get("href"), "/", 2) != -1:
                    badURL = True
                    break
           

            if not badURL:
                print("Got link: " + link.get("href"))
                if "logout" in link.get("href") or "log_out" in link.get("href") or "signout" in link.get("href"):
                    print("Flagged as potential logout link. Not adding to auth URLs.")
                else:
                    authURLs.append(link.get("href"))
                urls.append(link.get("href"))
                
                

        
def crawlLoginPage(site):
    global urls
    global authURLs

    # To make things easier.
    url = baseURL + site
    
    print("Found a login page that requires authentication.")
    print("Please enter your username and password")
    cj = cookiejar.CookieJar()
    br = mechanize.Browser()
    br.set_cookiejar(cj)
    br.open(url)

    br.select_form(nr=0)
    br.form["username"] = input("Username: ")
    br.form["password"] = input("Password: ")

    br.submit()

    if br.response().code != 200:
        print("The system did not receive a response. Unable to continue crawling past login page. Status code: " + str(br.response().code))
        return

    print("Redirected to " + br.response().geturl())    
    if br.response().geturl() == url:
        print("Login failed. Please double check your credentials.")
        crawlLoginPage(url)
        return

    print("Crawling sub URL: " + br.response().geturl())
    urls.append(url)
    
    crawlHTML(br.response().read())

    for item in authURLs:
        br.open(baseURL + item)
        if br.response().geturl() == url:
            print("Unable to proceed to URL " + url + ". Perhaps the request was logged out.")
            return
        if br.response().code != 200:
            print("The system did not receive a response. Unable to continue crawling past login page. Status code: " + str(br.response().code))
            return

        crawlHTML(br.response().read())

    print("Finished crawling authenticated HTML.")
    

    
def crawlLink(url):
    print("Crawling URL: " + url)
    global urls
    
    reqs = requests.get(url)
    soup = BeautifulSoup(reqs.text, 'html.parser')

    for link in soup.find_all('a'):
        if link.get("href") != "#" and link.get("href") not in urls and "http" not in link.get("href"):
            print("Got link: " + link.get("href"))
            urls.append(link.get("href"))
            if link.get("href") == "/login" or link.get("href") == "signin":
                crawlLoginPage(link.get("href"))
            else:
                crawlLink(baseURL + link.get("href"))

starttime = time.time()

urls.append("/")
crawlLink(baseURL)

endtime = time.time() - starttime

print("=====================================================")
print("Crawling completed in " + str(round(endtime)) + " seconds.")
print("Found a total of " + str(len(urls)) + " URLs.")
print("Full list of URLs is below (with authenticated ones noted):")
for item in urls:
    if item in authURLs:
        print(baseURL + item + " (authenticated)")
    else:
        print(baseURL + item)
