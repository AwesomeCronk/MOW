import random, time
from datetime import datetime, timedelta, timezone
from threading import Thread

from utils import dbBotData, dbQOTD

from __main__ import runFlag

def autopostQOTD():
    while runFlag:
        if dbBotData.get('qotdEnabled') == b'yes':

            now = datetime.now(timezone.utc())
            timestamp = datetime.fromtimestamp(int.from_bytes(dbQOTD.get(timestamp), 'big'))
            
            if now > timestamp + timedelta(hours=6) and 6 <= now.hour <= 7:
                dbQuestions = dbQOTD.node('questions')
                current = int.from_bytes(dbQOTD.get('current'), 'big') + 1
                
                for nodeID in dbQuestions.nodes:
                    dbQuestion = dbQuestions.node(nodeID)

                    if int.from_bytes(dbQuestion.get('timesAsked'), 'big') == 0:
                        selectedQuestionID = nodeID
                        break
                else:
                    minAge = int.from_bytes(dbQOTD.get('minAge'), 'big')
                    for i in range(100):
                        selectedQuestionID = random.choice(dbQuestions.nodes)
                        dbQuestion = dbQuestions.node(selectedQuestionID)
                        if current - int.from_bytes(dbQuestion.get('lastAsked'), 'big') >= minAge: break
                    else:
                        print('Unable to pick a suitable question')
                        selectedQuestionID = -1

                if selectedQuestionID != -1:
                    dbQuestion = dbQuestions.node(selectedQuestionID)
                    post = '<@{}> #{}: {}'.format(dbBotData.get('qotdRole').decode(), current, dbQuestion.get('question').decode())
                    print(post)  # Post the question
                    dbQuestion.set('lastAsked', int.to_bytes(current, 4, 'big'))
                    dbQuestion.set('timesAsked', int.to_bytes(int.from_bytes(dbQuestion.get('timesAsked') + 1, 'big'), 4, 'big'))

        
        # Loop every 3min, check runFlag every 5s
        for i in range(36):
            time.sleep(5)
            if not runFlag: break

def StartAutoQOTD():
    poster = Thread(target=autopostQOTD)
    poster.start()