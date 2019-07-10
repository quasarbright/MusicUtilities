import argparse
import xml.etree.ElementTree as ET
# import plistlib


parser = argparse.ArgumentParser(description="removes dead iTunes library references")
parser.add_argument('FILE', help="the Library.xml file representing your iTunes library")
arguments = parser.parse_args()
libraryFilePath = arguments.FILE
# with open(libraryFilePath, 'rb') as libraryFile:
#     pl = plistlib.load(libraryFile)
#     pl['Tracks']['1400']['Name'] = "not asphyxia lol"
#     with open('testOutputLibrary.xml', 'wb') as out:
#         plistlib.dump(pl, out)
tree = ET.parse(libraryFilePath)
root = tree.getroot()
root = root[0]

def allTags(element, tagsAccumulator=set([])):
    for child in element:
        tagsAccumulator.add(child.tag)
        allTags(child, tagsAccumulator)
    return tagsAccumulator

print(root.tag)

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
### left off here, about to make isValid accumulate a path for debugging


def isValid(element):
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
    '''
    # remember to recurse dict and array
    if element.tag not in ['dict', 'array']:
        return False, 'expected dict or array, got {0}'.format(element.tag)
    if len(element) % 2 != 0:
        return False, 'uneven children length'
    toRecurse = []
    if element.tag == 'dict':
        for i in range(len(element) // 2):
            keyIndex = i*2
            valueIndex = i*2 + 1
            key = element[keyIndex]
            if key.tag != 'key':
                return False, 'expected key tag, got {0}'.format(key.tag)
            value = element[keyIndex]
            if value.tag == 'key':
                return False, 'unexpected key'
            if value.tag in ['dict', 'array']:
                toRecurse.append(value)
    elif element.tag == 'array':
        for child in element:
            toRecurse.append(child)
    for child in toRecurse:
        if not isValid(child):
            return False
    return True

print(isValid(root))
    
    # use toRecurse

