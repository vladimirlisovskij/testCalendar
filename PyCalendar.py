#!/usr/bin/env python3
from __future__ import print_function

import datetime
import os.path
import pickle
import calendar
import argparse

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


def login():
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    root = "/root/testCalendar/"
    creds = None
    if os.path.exists(root + 'token.pickle'):
        with open(root + 'token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                root + 'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


def dateNowStr():
    return datetime.datetime.today().strftime("%D")


def makeDeck(date):
    day, month, year = date.day, date.month, date.year
    nowDay = datetime.datetime.today().day
    nowMonth = datetime.datetime.today().month
    nowYear = datetime.datetime.today().year
    weekday = datetime.date(year, month, 1).weekday()
    print("[now is " + dateNowStr() + "]    " + str(month) + "/" + str(year))
    print(" Mon Tue Wed Thu Fri Sat Sun")
    _, n = calendar.monthrange(year, month)
    deck = []
    for i in range(n):
        deck.append(str(i + 1))

    for i in range(weekday):
        deck.insert(0, '  ')

    for i in range(len(deck)):
        if deck[i] == str(nowDay) and month == nowMonth and year == nowYear:
            if len(deck[i]) == 1:
                print("[ " + deck[i] + "]", end='')
            else:
                print("[" + deck[i] + "]", end='')
        elif deck[i] == str(day):
            if len(deck[i]) == 1:
                print("! " + deck[i] + "!", end='')
            else:
                print("!" + deck[i] + "!", end='')
        else:
            if len(deck[i]) == 1:
                print("  " + deck[i] + " ", end='')
            else:
                print(" " + deck[i] + " ", end='')
        if (i + 1) % 7 == 0:
            print()
    print('\n')


def getDay(service, date, evtimemin=[0, 0, 0], evtimemax=[23, 59, 59]):
    day, month, year = date.day, date.month, date.year
    tmin = datetime.datetime(year, month, day, evtimemin[0], evtimemin[1], evtimemin[2]).isoformat() + "Z"
    tmax = datetime.datetime(year, month, day, evtimemax[0], evtimemax[1], evtimemax[2]).isoformat() + "Z"
    events_result = service.events().list(calendarId='primary',
                                          timeMin=tmin, timeMax=tmax,
                                          singleEvents=True,
                                          orderBy='startTime').execute()
    return events_result.get('items', [])


def makeCalendar(service, date):
    makeDeck(date)
    events = getDay(service, date)
    if len(events) == 0:
        print ("No events")
    else:
        for n, event in enumerate(events):
            print('[' + str(n) + '] ' + event['start']['dateTime'][11:19] + ' - ' + event['end']['dateTime'][11:19] + ': ', end = '')
            if 'summary' in event:
                print(event['summary'])
            else:
                print ('NoName')
            if 'description' in event:
                print(event['description'])
            print()


def makeDate(stringDate):
    listDate = list(map(int, stringDate.split(".")))
    if listDate[0] < 60:
        now = datetime.datetime.now()
       	listDate = [now.year, now.month, now.day] + listDate
    for i in range(6 - len(listDate)):
        listDate.append(0)
    date = datetime.datetime(listDate[0], listDate[1], listDate[2], listDate[3], listDate[4], listDate[5])
    return date.isoformat()

def main():
    service = build('calendar', 'v3', credentials=login())

    date = datetime.datetime.now()
    makeCalendar(service, date)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-swdate", help="Show date in format yy.mm.dd", type=str)
    parser.add_argument("-rmdate", help="To delete an event, enter a string in the format yy.mm.dd.n, where n is the number of the event", type=str)
    parser.add_argument("-mkdate", help="Flag to make the event", action='store_true')
    args = parser.parse_args()

    try:
    #if True:
        service = build('calendar', 'v3', credentials=login())
        if args.swdate:
            date = args.swdate.split(".")
            date = list(map(int, date))
            date = datetime.datetime(date[0], date[1], date[2])
            makeCalendar(service, date)
        elif args.rmdate:
            date = args.rmdate.split(".")
            date = list(map(int, date))
            if len(date) == 1:
                date, n = datetime.datetime.now(), date[0]
            else:
                date, n = datetime.datetime(date[0], date[1], date[2]), date[3]
            event = getDay(service, date)[n]
            print(event['start']['dateTime'][11:19] + ' - ' + event['end']['dateTime'][11:19] + ': ', end = '')
            print(event['summary']) if 'summary' in event else print ("NoName")
            if 'description' in event:
                print(event['description'])
            ans = input("You are exactly going to remove?(input 'y' to remove)\n")
            if ans == 'y':
                service.events().delete(calendarId='primary', eventId=event['id']).execute()
        elif args.mkdate:
            name = input("Input name of event\n")
            description = input("Input description of event\n")
            sdate = input("Input start of event\n")
            sdate = makeDate(sdate)

            edate = input("Input end of event\n")
            edate = makeDate(edate)

            event = {
                'summary': name,
                'description': description,
                'start': {
                    'dateTime': sdate,
                    'timeZone': 'Europe/Moscow'
                },
                'end': {
                    'dateTime': edate,
                    'timeZone': 'Europe/Moscow'
                }
            }

            event = service.events().insert(calendarId='primary', body=event).execute()

        else:
            date = datetime.datetime.now()
            makeCalendar(service, date)

    except Exception as e:
       print ("ERROR")
       print (str(e))
