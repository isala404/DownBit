import json
import feedparser
import time
import os

queue_template = {"Method": "Youtube",
                  "Name": "",
                  "URL": "",
                  "Quality": "",
                  "AddedTime": -1,
                  "CompletedTime": -1,
                  "Downloaded_Bytes": -1,
                  "Total_Bytes": -1,
                  "Mark_Watched": True,
                  "Playlist": [
                      {
                          "Start": 0,
                          "End": -1,
                          "Items": ""
                      }
                  ]
                  }


def youtube_crawler():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open('subscriptions/youtube.json') as f:
        for line in json.load(f):
            rss_feed = feedparser.parse(line['URL'])
            last_match = -1
            for i, entry in enumerate(rss_feed['entries']):
                if entry['link'] == line['Last Video']:
                    break
                last_match = i

            # Prevent Downloading whole list if last match is missing
            # This may happen if the creator delete the video
            if last_match > 6:
                last_match = 0

            for i in range(last_match, -1, -1):

                # Set the name
                if line['Includes'] == "" or is_match(rss_feed['entries'][i]['title'],
                                                      line['Includes'], line["Excludes"]):
                    queue_template['Name'] = rss_feed['entries'][i]['title']
                    queue_template['URL'] = rss_feed['entries'][i]['link']
                    queue_template['Quality'] = line['Quality']
                    queue_template['Path'] = line['Path']
                    queue_template['AddedTime'] = str(time.time())
                    queue_template['Mark_Watched'] = line['Mark Watched']
                    # TODO : Add Total_Bytes

                    path2queue = os.path.join(current_dir, '../queue')

                    file_name = "item_{}.json".format(len(os.listdir(path2queue)) + 1)
                    file_name = os.path.join(path2queue, file_name)

                    while os.path.isfile(file_name):
                        file_name = "item_{}.json".format(len(os.listdir(path2queue)) + 1)
                        file_name = os.path.join(path2queue, file_name)
                        # TODO: LOG this event

                    with open(file_name, 'w') as f:
                        json.dump(queue_template, f)


def is_match(name, includes, excludes):
    ins_matched = False
    exes_matched = False
    brake_main = False
    for ins in includes.split('||'):
        for include in ins.split(','):
            if not include.lower().strip() in name.lower():
                ins_matched = False
                break
            else:
                ins_matched = True
        if ins_matched:
            brake_main = True
        else:
            if brake_main:
                break
            else:
                continue
    if excludes != '':
        for exclude in excludes.split(','):
            if exclude.lower().strip() in name.lower():
                exes_matched = True
                break
            else:
                exes_matched = False
    if ins_matched and not exes_matched:
        return True
    else:
        return False
