from bs4 import BeautifulSoup
from urllib2 import urlopen
from datetime import datetime
import csv
import sys
import os
import smtplib
import config
import pprint

# Craigslist search URL
BASE_URL = ('https://chicago.craigslist.org/search/'
            '?sort=rel&areaID=11&subAreaID=&query={0}&catAbb=sss')
# BASE_URL = ('https://chicago.craigslist.org/search/ccc?query=dog%20labrador&sort=rel')
# BASE_URL = ("https://sfbay.craigslist.org/i/motorcycles")
# BASE_URL = ("http://sfbay.craigslist.org/search/mcy?auto_make_model=suzuki+drz")

pp =pprint.PrettyPrinter(indent=4)

def parse_results(search_term):
    results = []
    search_term = search_term.strip().replace(' ', '+')
    search_url = BASE_URL.format(search_term)
    soup = BeautifulSoup(urlopen(search_url).read(), "lxml")
    rows = soup.find_all('a', class_="result-title hdrlnk")
    
    for row in rows:
        row_string = str(row)
        extension = row_string[row_string.find("href=")+6: row_string.find(".html") + 5]
        print extension.find("http")
        if extension.find("http") != 0:
            # tmp.append("http:chicago.craigslist.org" + extension)
            url = 'http://chicago.craigslist.org' + extension
            # url = 'http://sfbay.craigslist.org' + row.a['href']
            # price = row.find('span', class_='price').get_text()
            # create_date = row.find('time').get('datetime')
            # title = row.find_all('a')[1].get_text()
            # results.append({'url': url, 'create_date': create_date, 'title': title})
            results.append({'url': url, 'title': "NO_TITLE"})
    print("==========RESULTS==============")
    pp.pprint(results)
    print("+++++++++++END RESULTs++++++++++")
    return results

def write_results(results):
    """Writes list of dictionaries to file."""
    fields = results[0].keys()
    with open('results.csv', 'w') as f:
        dw = csv.DictWriter(f, fieldnames=fields, delimiter='|')
        dw.writer.writerow(dw.fieldnames)
        dw.writerows(results)

def has_new_records(results):
    # DEBUG
    # print (results)
    if len(results) > 0:
        current_posts = [x['url'] for x in results]
        fields = results[0].keys()
        if not os.path.exists('results.csv'):
            return True

        with open('results.csv', 'r') as f:
            reader = csv.DictReader(f, fieldnames=fields, delimiter='|')
            seen_posts = [row['url'] for row in reader]

        is_new = False
        for post in current_posts:
            if post in seen_posts:
                pass
            else:
                is_new = True
    return is_new

def send_text(phone_number, msg):
    fromaddr = "Craigslist Checker"
    toaddrs = phone_number + "@txt.att.net"
    msg = ("From: {0}\r\nTo: {1}\r\n\r\n{2}").format(fromaddr, toaddrs, msg)
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(config.email['username'], config.email['password'])
    server.sendmail(fromaddr, toaddrs, msg)
    server.quit()

def get_current_time():
    return datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')

if __name__ == '__main__':
    try:
        TERM = sys.argv[1]
        PHONE_NUMBER = sys.argv[2].strip().replace('-', '')
    except:
        print "You need to include a search term and a 10-digit phone number!\n"
        sys.exit(1)

    if len(PHONE_NUMBER) != 10:
        print "Phone numbers must be 10 digits!\n"
        sys.exit(1)

    results = parse_results(TERM)
    print "type(results) = " + str(type(results))
    if results is None:
        print("106 ERROR--> exiting because results is type NoneType")
        exit
    # Send the SMS message if there are new results
    elif has_new_records(results):
        message = "Hey - there are new Craigslist posts for: {0}".format(TERM.strip())
        print "[{0}] There are new results - sending text message to {0}".format(get_current_time(), PHONE_NUMBER)
        send_text(PHONE_NUMBER, message)
        write_results(results)
    else:
        print "[{0}] No new results - will try again later".format(get_current_time())
