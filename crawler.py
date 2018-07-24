import re
import urllib
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import urllib.request as requester
import traceback
import requests

apiPrevData = [
{
 "pageURL": "http://bbmp.gov.in/en/about-us",
 'Link': 'http://www.discoverbangalore.com/History.htm',
 'Text': 'www.discoverbangalore.com'
},
{
 "pageURL": "http://bbmp.gov.in/en/web/guest/engineering",
 'Link': 'de',
 'Text': 'dssd'
},
]

class WebCrawl:
    def __init__(self, web_link, *args,**kwargs):
        super(WebCrawl,self).__init__(*args,**kwargs)
        self.web_url = self.web_url_root = web_link
        self.visited = dict() #To track visited
        self.handleHomePageLinks()
    
    def handleHomePageLinks(self):
        self.visited["http://bbmp.gov.in/en/web/guest/home"] = 1
        self.visited["http://bbmp.gov.in/kn_IN/home"] = 1
        
    def getHrefDictionary(self, url_response):
        response = dict()
        html_parse = BeautifulSoup(url_response)
        for atag in html_parse.findAll('a'):
#             astr = str(atag)
#             astr = re.sub(r'\s+', ' ', astr)
#             print(astr)
            try:
                key = atag['href']
                #make url's absolute if found relative
                if (urlparse(atag['href']).netloc == "") or (urlparse(self.web_url_root).netloc == urlparse(atag['href']).netloc):
                    key = urljoin(self.web_url_root,atag['href'])
                    
                key = key.split(";")[0]
                val = atag.text.strip()
                if val != "":
                    response[key] = val
            except:
                print(traceback.format_exc())
                pass
        return response
    
    def getDataFromApi(self, pageURL):
        pageURL = "hostname like bbmp.com"
        resp = requests.get('https://webcrawlerbackend.azurewebsites.net/api/getDataForPage?pageurl=' + pageURL)
        if resp.status_code != 200:
            print('Error: Server returned status code '.format(resp.status_code) )
            raise Exception
        return(resp.json())

#     def postDataToApi(self, retData):
#         resp = requests.post('', json=retData)
#         if resp.status_code != 200:
#             print('Error: Server returned status code '.format(resp.status_code) )
#             raise Exception


    def compareAndPush(self, page_url, page_links):
        apiData = self.getDataFromApi(page_url)
#         apiData = apiPrevData

        retData = {
                'pageURL': page_url,
                'insert':{},
                'delete':{}
                }

        prevLink = []
        prevText = []
        for apiObj in apiData['pages']:
            prevLink.append(apiObj['linkUrl'])
            prevText.append(apiObj['linktext'])    

        #Added
        for key, value in page_links.items():
            print("Harsh key=" + key + " val=" + value)
            if key not in prevLink:
                retData['insert'][key] = value

        i=0
        #Deleted
        while i < len(prevLink):
            if prevLink[i] not in page_links:
                retData['delete'][prevLink[i]] = prevText[i]            
            i = i+1

        #Print    
        print("INSERT")
        print(retData['insert'])

        print("DELETE")
        print(retData['delete'])

    #    postDataToApi(retData)
    
    
    def followLink(self,depth=1):
        if self.web_url in self.visited or depth < 1: return

        try:
            url_response = requester.urlopen(self.web_url,timeout=20)
            href_dict = self.getHrefDictionary(url_response)
            self.visited[self.web_url] = 1
            
            #call Harsh to push the changeset to backend service
            self.compareAndPush(self.web_url, href_dict)
            
            for key, value in href_dict.items():
                if key.startswith('http://bbmp.gov.in/en'):
                    print("Rajat key = " + key + " value = " + value)
                    self.web_url = key
                    self.followLink(depth-1)
        except Exception as e:
            print("ERROR: Could not open {0}: {1}".format(self.web_url,e))
            return
        
        return
