import praw
import requests
import os
import math
from collections import deque
import datetime
import re

#Initialize reddit
r=praw.Reddit(user_agent="/r/Futurology Rule 13 bot by /u/captainmeta4")
username = "Rule_13_Bot"

#Embed.ly stuff
key= os.environ.get('key')

class Bot():

    def initialize(self):
        r.login(username,os.environ.get('password'))

        self.already_done=deque([],maxlen=200)

    def process_submissions(self):

        for submission in praw.helpers.submission_stream(r,"futurology",limit=100, verbosity=0):

            #Avoid duplicate work
            if submission.id in self.already_done:
                continue

            self.already_done.append(submission.id)

            print("checking "+submission.title)

            #ignore self_posts:
            if submission.is_self:
                continue

            #Get the submission url
            url=submission.url

            #Create params
            params={'url':url,'key':key}

            #Hit the embed.ly API for data
            data=requests.get('http://api.embed.ly/1/extract',params=params)

            #Get timestamp
            content_creation = data.json()['published']

            #Pass on content that does not have a timestamp
            if content_creation == None:
                continue

            #Divide the creation timestamp by 1000 because embed.ly adds 3 extra zeros for no reason
            content_creation = content_creation / 1000
            
            #sanity check for when embed.ly fucks up the timestamp - ignore the post
            if content_creation < 0:
                continue

            #Get the reddit submission timestamp
            post_creation = submission.created_utc

            #Find content age, in days
            age = math.floor((post_creation - content_creation) / (60 * 60 * 24))

            #Pass on submissions less than six months old - guaranteed to follow the rule
            if age < 182:
                continue

            #Convert timestamp to date object
            post_date = datetime.date.fromtimestamp(content_creation)

            #Get possible month strings to look for in title
            months=[]
            months.append(post_date.strftime('%b')) #Month abbreviated name (Jan, Feb, Mar)
            months.append(post_date.strftime('%B')) #Month full name (January, February, March)
            months.append(post_date.strftime('%m')) #Month number (01, 02, 03)

            #Get possible year strings to look for in title
            years=[]
            years.append(post_date.strftime('%y')) #2 digit year (98, 99, 00, 01)
            years.append(post_date.strftime('%Y')) #4 digit year (1998, 1999, 2000, 2001)

            #We're looking for "[month, year]" in the title, so generate a regex to find that
            regex= "\[ ?("+months[0]+'|'+months[1]+'|'+months[2]+'),? ('+years[0]+'|'+years[1]+') ?\]'

            #See if month/year tag is present in title
            if re.search(regex, submission.title) != None:
                continue

            #At this point we know the post breaks rule 13
            print("http://redd.it/"+submission.id+" - "+submission.title)

            #Set removed flair
            submission.set_flair(flair_text="Rule 13",flair_css_class="removed")

            #Remove the submission
            submission.remove()

            #Generate a URL that can be clicked to submit with proper title
            params = {'url':submission.url, 'title': "["+months[1]+" "+years[1]+"] "+submission.title, 'resubmit':True}
            
            link=requests.get('http://www.reddit.com/r/Futurology/submit',params=params).url
            
            #Leave a distinguished message
            msg=("Thanks for contributing. However, your submission has been automatically removed:\n\n"+
                 "> **Rule 13:** Content older than 6 months must have [month, year] in the title.\n\n"+
                 "Please click here to resubmit with an acceptable title:\n\n>["+params['title']+"]("+link+")\n\n"+
                 "Please refer to the [subreddit rules](/r/futurology/wiki/rules) for more information.\n\n---\n\n"+
                 "*I am a bot. Please [Message the Mods](https://www.reddit.com/message/compose?to=/r/"+submission.subreddit.display_name+
                 "&subject=Question regarding the removal of this submission by /u/"+submission.author.name+
                 "&message=I have a question regarding the removal of this [submission]("+submission.permalink+") if you feel this was in error.*")

            submission.add_comment(msg).distinguish()

if __name__=='__main__':
    modbot=Bot()
    modbot.initialize()
    modbot.process_submissions()
