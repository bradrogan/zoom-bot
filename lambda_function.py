import os
import json
from datetime import timezone, datetime
from botocore.vendored import requests
import boto3
import tempfile
import logging
import dateutil.parser

config_bucket = os.environ['CONFIG_BUCKET']
config_key = os.environ['CONFIG_KEY']
short_meeting_threshold_sec = int(os.environ['SHORT_MEETING_THRESHOLD_SEC'])


def find_meeting(topic_name):
    
    s3 = boto3.client('s3')
    configF = s3.get_object(Bucket=config_bucket, Key=config_key)
    
    config = configF['Body'].read()
    
    config_json = json.loads(config)
    
    return next(d for d in config_json['meetings'] if d['topic'].upper() == topic_name.upper() ) 
    
def build_message(title, tags, startTime, endTime, topic, url):
    tagString = ','.join(map(str, tags)) 

    start = '<!date^' + str(int(startTime.timestamp())) + '^{date_short} at {time}|' + "Your Slack client is too old for times" + '>'

    end = '<!date^' + str(int(endTime.timestamp())) + '^{date_short} at {time}|' + "Your Slack client is too old for times" + '>'
    
    message = {'blocks':'[{"type":"section","text":{"type":"mrkdwn","text":"' + title + ':\n*<' + url + '|Meeting Recording>*"}},{"type":"section","fields":[{"type":"mrkdwn","text":"*Start Time*\n' + start + '"},{"type":"mrkdwn","text":"*End Time:*\n' + end + '"},{"type":"mrkdwn","text":"*Topic:*\n' + topic + '"},{"type":"mrkdwn","text":"*Who cares!?*\n' + tagString + '"}]}]'}

    return message

        
def lambda_handler(event, context):
    
    logging.getLogger().setLevel(logging.INFO)
    
    recording_type='shared_screen_with_speaker_view'
    
    #get all the info from the Zoom webhook body
    body = json.loads(event['body'])
    
    logging.info('Zoom Request Body' + json.dumps(body))
    
    obj = body['payload']['object']
    topic = obj['topic']
    host = obj['host_email']
    
    recording = next(d for d in obj['recording_files'] if d['recording_type'].upper() == recording_type.upper() ) 
    
    start = datetime.strptime(recording['recording_start'],'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    end = datetime.strptime(recording['recording_end'],'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    meeting_url = recording['play_url']
    
    duration = end - start
    
    #only try send a message if the meeting lasted longer than a minute (people join the wrong meeting ALL the time)
    if duration.total_seconds() > short_meeting_threshold_sec:
        #try and find the meeting in the config file
        try:
            config = find_meeting(topic)
        except:
            logging.info('Meeting not found: ' + topic)
            return {
                'statusCode': 500,
                'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': 'Meeting not found'})
            }
        
        #set the Slack webhook url
        hook = config['slackchannelhook']
        
        #set the Slack message title
        msg = config['slackmessagetitle']
        
        #now grab all the users we will tag in the message
        slack_tagged_users = []
        
        for u in config['slackusers']:
            slack_tagged_users.append('<@' + u['slackid'] + '>')
            
        slack_data = build_message(msg, slack_tagged_users, start, end, topic, meeting_url)
        
        slack_headers =  {'content-type':'application/json'}
        
        sr = requests.post(hook, headers=slack_headers, json=slack_data)
        
        if not sr.ok:
            logging.error('ERROR: Slack API Call not successful.\n\n')
            return {
                'statusCode': 500,
                'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': 'Slack Call Failed'})
            }
        else:
            logging.info('Slack call succeeded for ' + topic)
        
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'status': 'Slack message sent'})
            }
    else:
        logging.info('Short Meeting Threshold filtered out meeting: ' + topic)
