import json
import sqlite3
import requests
import re
from bs4 import BeautifulSoup 
from datetime import datetime
from urllib.request import urlopen

def get_jsonparsed_data(url):
    response = urlopen(url)
    data = response.read().decode("utf-8")
    return json.loads(data)

def getSecurityCode():
    try:
        page = requests.get('https://upullitne.com/')
        soup = BeautifulSoup(page.content, 'html.parser')
        content = soup.find(id='sif_plugin js frontend main-js-extra').text

        search = r"\"sif_ajax_nonce\":\".{10}\""
        securitycode = re.findall(search, str(content))[0]
        
        return(securitycode[18:28])
    except:
        print("Could not get security token!")
        return(0)


# Get the JSON data from the website
verify_token = getSecurityCode()
url = "https://upullitne.com/wp-admin/admin-ajax.php?action=sif_search_products&sif_verify_request=" + verify_token + "&sorting[key]=batch_number"
cars = get_jsonparsed_data(url)

logfile = open("upullit-log.txt", "a")
logfile.write("[" + str(datetime.now()) + "] Begin scraping\n")

# Get a dictionary of new cars
newcars=[]
newcarsindex=[]
for car in cars['products']:
    d={}
    d['batch_number']=car['batch_number']
    d['make']=car['make']
    d['model']=car['model']
    d['iyear']=car['iyear']
    d['color']=car['color']
    d['vehicle_row']=car['vehicle_row']
    d['yard_date']=car['yard_date']

    newcars.append(d)
    newcarsindex.append(car['batch_number'])

# Get a dictionary of previously scraped cars
conn = sqlite3.connect("upullit-data.db")
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS \"upullit_cars\" (batch_number TEXT, make TEXT, model TEXT, year INTEGER, color TEXT, vehicle_row INTEGER, yard_date TEXT)")
cur.execute("SELECT * FROM upullit_cars")

rows = cur.fetchall()

oldcars=[]
oldcarsindex=[]
for car in rows:
    d={}
    d['batch_number']=car[0]
    d['make']=car[1]
    d['model']=car[2]
    d['iyear']=car[3]
    d['color']=car[4]
    d['vehicle_row']=car[5]
    d['yard_date']=car[6]
    
    oldcars.append(d)
    oldcarsindex.append(car[0])


# Add new cars to database
newcarlist = set(newcarsindex).difference(set(oldcarsindex))

if (len(newcarlist) > 0):
    for car in newcars:
        for index in newcarlist:   
            if car['batch_number'] == index:
                try:
                    cur.execute("INSERT INTO upullit_cars VALUES (?, ?, ?, ?, ?, ?, ?)", (car['batch_number'], car['make'], car['model'], str(car['iyear']), car['color'], str(car['vehicle_row']), car['yard_date']))
                    print("NEW: ", car['iyear'], car['make'], car['model'], car['color'], car['yard_date'], car['vehicle_row'], "added to lot.")
                    logfile.write("[" + str(datetime.now()) + "] NEW: " + car['iyear'] + " " + car['make'] + " " +  car['model'] + " " +  car['color'] + " " +  car['yard_date'] + " " +  car['vehicle_row'] + " added to lot.\n")
                except:
                    print("Could not add record to database.")
                    logfile.write("Could not add record to database.\n")
    
    print(str(len(newcarlist)) + " cars added to lot.")
    logfile.write("[" + str(datetime.now()) + "] " + str(len(newcarlist)) + " cars added to lot.\n")
else:
    logfile.write("[" + str(datetime.now()) + "] No cars added to lot.\n")

# Remove cars that weren't on the website from the database
oldcarlist = set(oldcarsindex).difference(set(newcarsindex))

if (len(oldcarlist) > 0):
    for car in oldcars:
        for index in oldcarlist:
            if car['batch_number'] == index:
                try:
                    cur.execute("DELETE FROM upullit_cars WHERE batch_number = ?", (car['batch_number'],))
                    print("REMOVED: ", car['iyear'], car['make'], car['model'], car['color'], car['yard_date'], car['vehicle_row'], "removed from lot.")
                    logfile.write("[" + str(datetime.now()) + "] REMOVED: " + str(car['iyear']) + " " + car['make'] + " " + car['model'] + " " + car['color'] + " " + car['yard_date'] + " " + str(car['vehicle_row']) + " removed from lot.\n")
                except:
                    print("Could not delete record from database.")
                    logfile.write("Could not delete record from database.\n")


    print(str(len(oldcarlist)) + " cars removed from lot.")
    logfile.write("[" + str(datetime.now()) + "] " + str(len(oldcarlist)) + " cars removed from lot.\n")
else:
    logfile.write("[" + str(datetime.now()) + "] No cars removed from lot.\n")

logfile.write("\n")
logfile.close()
conn.commit()
conn.close()
