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
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
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
    weekday = datetime.date(year, month, 1).weekday()
    print(f"[now is {dateNowStr()}]    {month}/{year}")
    print(" Mon Tue Wed Thu Fri Sat Sun")
    _, n = calendar.monthrange(year, month)
    deck = []
    for i in range(n):
        deck.append(str(i + 1))

    for i in range(weekday):
        deck.insert(0, '  ')

    for i in range(len(deck)):
        if deck[i] == str(nowDay):
            if len(deck[i]) == 1:
                print(f"[ {deck[i]}]", end='')
            else:
                print(f"[{deck[i]}]", end='')
        elif deck[i] == str(day):
            if len(deck[i]) == 1:
                print(f"! {deck[i]}!", end='')
            else:
                print(f"!{deck[i]}!", end='')
        else:
            if len(deck[i]) == 1:
                print(f"  {deck[i]} ", end='')
            else:
                print(f" {deck[i]} ", end='')
        if (i + 1) % 7 == 0:
            print()
    print('\n')


def getday(service, date, evtimemin=[0, 0, 0], evtimemax=[23, 59, 59]):
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
    events = getday(service, date)
    for n, event in enumerate(events):
        # start = event['start'].get('dateTime', event['start'].get('date'))
        # print (event)
        print(f'[{n}] ' + event['start']['dateTime'][11:19] + ' - ' + event['end']['dateTime'][11:19] + ': ' + event[
            'summary'])
        if 'description' in event:
            print(event['description'])
        print()

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
        service = build('calendar', 'v3', credentials=login())
        if args.swdate:
            date = args.swdate.split(".")
            date = list(map(int, date))
            date = datetime.datetime(date[0], date[1], date[2])
            makeCalendar(service, date)
        elif args.rmdate:
            date = args.rmdate.split(".")
            date = list(map(int, date))
            date, n = datetime.datetime(date[0], date[1], date[2]), date[3]
            event = getday(service, date)[n]
            print(event['start']['dateTime'][11:19] + ' - ' + event['end']['dateTime'][11:19] + ': ' + event[
                    'summary'])
            if 'description' in event:
                print(event['description'])
            ans = input("You are exactly going to remove?(input 'y' to remove)\n")
            if ans == 'y':
                service.events().delete(calendarId='primary', eventId=event['id']).execute()
        elif args.mkdate:
            name = input("Input name of event\n")
            description = input("Input description of event\n")
            sdate = input("Input start of event\n")
            sdate = sdate.split(".")
            sdate = list(map(int, sdate))
            sdate = datetime.datetime(sdate[0], sdate[1], sdate[2], sdate[3], sdate[4], sdate[5]).isoformat()

            edate = input("Input end of event\n")
            edate = edate.split(".")
            edate = list(map(int, edate))
            edate = datetime.datetime(edate[0], edate[1], edate[2], edate[3], edate[4], edate[5]).isoformat()

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
        print(str(e))