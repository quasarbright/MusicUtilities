'''
decided on just doing it the iTunes way. This script is not finished
'''
from typing import List
import os
import argparse
import re
from urllib.parse import unquote
# import plistlib


parser = argparse.ArgumentParser(
    description="removes dead iTunes library references")
parser.add_argument(
    'FILE', help="the Library.xml file representing your iTunes library")

arguments = parser.parse_args()
libraryFilePath = arguments.FILE
libraryContents = ''
with open(libraryFilePath, 'r', encoding='UTF-8') as f:
    libraryContents = f.read()

songRegex = r'<key>\d*</key>\s*<dict>[\s\S]*?</dict>'

def doesUriExist(uri):
    finalPath = unquote(uri)
    finalPath = finalPath.replace('file://localhost/', '')
    finalPath = os.path.join(finalPath)
    ans = os.path.isfile(finalPath)
    return ans

def getAllSongMatches() -> List[str]:
    matchIter = re.finditer(songRegex, libraryContents)
    matches = []
    for match in matchIter:
        matches.append(match)
    return matches

liveCount = 0
deadCount = 0
for songMatch in getAllSongMatches():
    locationRegex = r'<key>Location</key><string>(.*?)</string>'
    songGroup = songMatch.group()
    locationMatch = re.search(locationRegex, songGroup)
    assert locationMatch is not None
    uri = locationMatch.group(1)
    if doesUriExist(uri):
        liveCount += 1
    else:
        deadCount += 1
        pat = r'<key>Name</key><string>(.*?)</string>'
        match = re.search(pat, songGroup)
        if match is not None:
            print(match.group(1), uri)
print('live', liveCount)
print('dead', deadCount)

