import os
import argparse
import xml.etree.ElementTree as ET
from urllib.parse import unquote
# import plistlib


parser = argparse.ArgumentParser(description="removes dead iTunes library references")
parser.add_argument('FILE', help="the Library.xml file representing your iTunes library")
arguments = parser.parse_args()
libraryFilePath = arguments.FILE

tree = ET.parse(libraryFilePath)
root = tree.getroot()
root = root[0]

def allTags(element, tagsAccumulator=set([])):
    for child in element:
        tagsAccumulator.add(child.tag)
        allTags(child, tagsAccumulator)
    return tagsAccumulator

def followIndexPath(path):
    '''path is list of indices
    returns the element reached by following the indices
    does not know about dict, just does raw xml child indices'''
    element = root
    for loopIndex, pathIndex in enumerate(path):
        if pathIndex >= len(element):
            raise ValueError('path {0} does not exist'.format(path[:loopIndex-1]))
        else:
            element = element[pathIndex]
    return element


def isValid(element, pathSoFar=[]):
    '''
    element is an xml tree element
    it should be a dict tag or array
    recurses depth first

    valid is 
    <dict>
        <key></key><value></value>
        <key></key><value></value>
        ...
    </dict>
    or
    <array>
        <dict></dict>
        <dict></dict>
        ...
    </array>
    '''
    # remember to recurse dict and array
    if element.tag not in ['dict', 'array']:
        return False, 'expected dict or array, got {0}. path: {1}'.format(element.tag, pathSoFar)
    toRecurse = [] # [(element, path), ...]
    if element.tag == 'dict':
        if len(element) % 2 != 0:
            return False, 'uneven children length for dict. path: {0}'.format(pathSoFar)
        for i in range(len(element) // 2):
            keyIndex = i*2
            valueIndex = i*2 + 1

            newPath = pathSoFar[:]
            newPath.append(valueIndex)

            key = element[keyIndex]
            if key.tag != 'key':
                return False, 'expected key tag, got {0}. path: {1}'.format(key.tag, newPath)
            value = element[valueIndex]
            if value.tag == 'key':
                return False, 'unexpected key. path: {0}'.format(newPath)
            if value.tag in ['dict', 'array']:
                toRecurse.append((value, newPath))
    elif element.tag == 'array':
        for index, child in enumerate(element):
            childPath = pathSoFar[:]
            childPath.append(index)
            toRecurse.append((child, childPath))
    for child, childPath in toRecurse:
        isChildValid, msg = isValid(child, childPath)
        if not isChildValid:
            return False, msg
    return True, ''

def printTagAndText(element):
    print('<{0}>{1}</{0}>'.format(element.tag, element.text))

def getAllTrackElements():
    for index, child in enumerate(root):
        if child.tag == 'key' and child.text == 'Tracks':
            return root[index+1]

def getAllPlaylistElements():
    for index, child in enumerate(root):
        if child.tag == 'key' and child.text == 'Playlists':
            return root[index+1]

def dictIter(element):
    assertDict(element)
    ans = []
    for keyIndex in range(0, len(element), 2):
        valueIndex = keyIndex+1
        key = element[keyIndex]
        value = element[valueIndex]
        ans.append((key, value))
    return ans

def assertDict(element):
    if not element.tag == 'dict':
        raise ValueError('element must be dict: {}'.format(element))
    validation = isValid(element)
    if not validation[0]:
        raise ValueError("element must be valid dict: {}. msg: {}".format(
            element, validation[1]))

def getDictValue(element, key):
    '''key: string
    returns: element'''
    assertDict(element)
    for currentKey, currentValue in dictIter(element):
        if currentKey.text == key:
            return currentValue
    raise KeyError("key '{}' not found in {}".format(key, element))

def toPy(element):
    '''converts element to python dict or list
    please do not try to convert back it will be annoying'''
    validation = isValid(element)
    if not validation[0]:
        raise ValueError(validation[1])
    if element.tag == 'array':
        ans = []
        for child in element:
            ans.append(toPy(child))
        return ans
    elif element.tag == 'dict':
        ans = {}
        for key, value in dictIter(element):
            if value.tag in ['array', 'dict']:
                ans[key.text] = toPy(value)
            else:
                ans[key.text] = value.text
        return ans
            

def getAllTrackNames():
    trackNames = []
    allTracks = getAllTrackElements()
    for trackId, trackDict in dictIter(allTracks):
        for key, value in dictIter(trackDict):
            if key.text == "Name":
                trackNames.append(value.text)
    return trackNames

def dumpNSongs(n):
    allTracks = getAllTrackElements()
    count = 0
    for trackId, trackDict in dictIter(allTracks):
        if count == n:
            break
        ET.dump(trackDict)
        count += 1

def doesUriExist(uri):
    finalPath = unquote(uri)
    finalPath = finalPath.replace('file://localhost/', '')
    finalPath = os.path.join(finalPath)
    ans = os.path.isfile(finalPath)
    return ans

def doesSongElementHaveValidLink(element):
    '''
    expects element to be the dict of a song
    (should have mp3 metadata as keys)
    '''
    assertDict(element)
    location = getDictValue(element, 'Location')
    location = location.text
    return doesUriExist(location)

def getSongById(id):
    '''id: track id int or int string
    returns song element dict'''
    for trackId, trackDict in dictIter(getAllTrackElements()):
        if trackId.text == str(id):
            return trackDict
    raise ValueError('id not found: {}'.format(id))

def doesSongIdHaveValidLink(id):
    '''expects track id as int'''
    song = getSongById(id)
    return doesSongElementHaveValidLink(song)


def removeSong(id):
    '''removes all instances of the track
    id: int or int string track id'''
    # remove from all tracks
    allSongs = getAllTrackElements()
    for trackId, trackDict in dictIter(allSongs):
        if trackId.text == str(id):
            # remove trackId and trackDict elements
            allSongs.remove(trackId)
            allSongs.remove(trackDict)
    # remove from playlists
    allPlaylists = getAllPlaylistElements()
    for playlist in allPlaylists:
        try:
            items = getDictValue(playlist, 'Playlist Items')
        except KeyError:
            # playlist is empty
            continue
        for item in items:
            # each item is <dict><key>Track ID</key><integer>1234</integer></dict>
            trackId = getDictValue(item, 'Track ID')
            if trackId.text == str(id):
                items.remove(item)

def removeDeads():
    '''removes all dead song elemements in place'''
    for trackId, trackDict in dictIter(getAllTrackElements()):
        if not doesSongElementHaveValidLink(trackDict):
            # dead link. remove from library
            removeSong(int(trackId.text))


def writeToTest():
    tree.write('testOutputLibrary.xml')

removeDeads()
writeToTest()
print()