import requests
from bs4 import BeautifulSoup
import mysql.connector
from mysql.connector import errorcode
from datetime import datetime

import config
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def parse_month(URL, playerdict):
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find(id = 'transactions')
    transactions = results.find_all('td', class_='description')
    for transaction in transactions:
        players = transaction.find('a')
        if players is not None:
            for player in players:
                if player in playerdict:
                    playerdict[player] += 1
                else:
                    playerdict[player] = 1

def create_url(month, year):
    return 'https://www.mlb.com/phillies/roster/transactions/' + str(year) + '/' + str(month)

def main():
    playerdict = {}
    parse_month(create_url('09', 2020), playerdict)
    parse_month(create_url(10, 2020), playerdict)
    parse_month(create_url(11, 2020), playerdict)
    parse_month(create_url(12, 2020), playerdict)

    currentmonth = datetime.now().month
    for i in range(int(currentmonth)):
        i += 1
        if i < 10:
            i = str(i)  
            i = "0" + i
        else:
            i = str(i)
        parse_month(create_url(i, 2021), playerdict)

    sendemail = False
    sendplayers = []
    try:
        cnx = mysql.connector.connect(user=config.username, password=config.password,
                                host='127.0.0.1', database=config.databaseName)
        cursor = cnx.cursor()
        for playername in playerdict:
            amount = playerdict[playername]
            if "\'" in playername:
                playername = playername.split('\'')
                playername = playername[0] + ' ' + playername[1]
            cursor.execute("""SELECT * FROM players WHERE name = '%s'""" % playername)
            result = cursor.fetchall()
            if result == []:
                print("New Player Detected: " + playername)
                sendplayers.append(playername)
                sendemail = True
                try:
                    sql = "INSERT INTO players (name, frequency) VALUES (%s, %s)"
                    val = (playername, str(amount))
                    cursor.execute(sql, val)
                    cnx.commit()
                except:
                    print("Failed")
            else:
                for x in result:
                    if x[2] == amount:
                        continue
                    else:
                        print("New Transaction Detected: " + playername)
                        sendplayers.append(playername)
                        try:
                            cursor.execute("""SELECT playerid FROM players WHERE name = '%s'""" % playername)
                            result = cursor.fetchall()
                            result = result[0][0]

                            sql = "UPDATE players SET frequency = %s WHERE playerid = %s"
                            val = (str(amount), str(result))
                            cursor.execute(sql, val)
                            cnx.commit()
                        except:
                            print("Failed")
                        sendemail = True

        cnx.close()
        if not sendemail:
            print("No New Transactions")

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)


    if sendemail:
        body = "New transactions detected:\n"
        for player in sendplayers:
            body += str(player) +"\n"
        body += "\nhttps://www.mlb.com/phillies/roster/transactions"
        subject = "New Phillies Transaction!"

        msg = MIMEMultipart()
        msg['From'] = config.mailFromAdress
        msg['To'] = config.mailToAdress
        msg['Subject'] = subject

        msg.attach(MIMEText(body,'plain'))
        message = msg.as_string()

        try:
            server = smtplib.SMTP(config.mailFromServer)
            server.starttls()
            server.login(config.mailFromAdress, config.mailFromPassword)

            server.sendmail(config.mailFromAdress, config.mailToAdress, message)
            server.quit()
            print("SUCCESS - Email sent")

        except Exception as e:
            print("FAILURE - Email not sent")
            print(e)
if __name__ == "__main__":
    main()
