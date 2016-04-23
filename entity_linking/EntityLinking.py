import urllib2
import urllib
import re
from lxml import html
import json
import threading
import sys, traceback
import operator


"""Entity Linker for a set of documents"""
#the set where 
typeDict = {}
docList = {}
dbpediaToFreebase = {}
threadNum = 5

def mapping(mapper):
    f = open(mapper)
    for line in f:
        segments = line.split(' ')
        dbID = segments[0][29:-1]
        fbID = segments[2][28:-1]
        dbpediaToFreebase[dbID] = fbID 

class myLinker (threading.Thread):
    docList = {}
    offset = 0
    confidence = 0
    def __init__(self, docList, offset, confidence):
        threading.Thread.__init__(self)
        self.docList = docList
        self.offset = offset
        self.confidence = confidence
    def run(self):
        print "Start DBpediaSpotlight"
        g = open('tmp/temp' + str(self.offset) + '.txt', 'w')
        index = 0
        while 1:
            did = str(index + self.offset)
            if did in self.docList:
                try:
                    doc = self.docList[did]
                    url = "http://spotlight.sztaki.hu:2222/rest/annotate"
                    #url = "http://localhost:2222/rest/annotate"
                    data = {"confidence":self.confidence}
                    data["support"] = "20"
                    data["text"] = doc;
                    data = urllib.urlencode(data)
                    req = urllib2.Request(url)
                    req.add_header('Accept', 'application/json') #text/xml')
                    # print did
                    page = html.fromstring(urllib2.urlopen(req, data, timeout=100).read())
                    docJson = html.tostring(page)[3:-4]
                    #print docJson
                    validEntities = extractAnnotations(docJson)
                    for entity in validEntities:
                        linkToFreebase(entity)
                        if (entity['@URI'] != None):
                            g.write(str(index + self.offset) + '\t' + entity['@surfaceForm'] + '\t' + entity['@URI'] + '\t'
                             + entity['@similarityScore'] + '\t' + entity['@percentageOfSecondRank']+ '\n')
                    index += threadNum
                except:
                    index += threadNum
                    print 'noresult'
            else:
                break
        g.close()


def link(docFile, confidence):
    # typeDict['m.01c5'] = None
    # read documents
    f = open(docFile)
    for doc in f:
        tab = doc.find('\t')
        did = doc[:tab]
        text = doc[tab+1:]
        docList[did] = text
    f.close()

    
    #for i in range(0, threadNum):
    #   print 'starrrrr'
    #   thread.start_new_thread( eachLinker, (i,) )
    threadLock = threading.Lock()
    threads = []

    for i in range(0, threadNum):
        mythread = myLinker(docList, i, confidence)
        mythread.start()
        threads.append(mythread)

    # Wait for all threads to complete
    for t in threads:
        t.join()

    print "Start joining the files"

    allLines = {}

    for i in range(0, threadNum):
        f = open('tmp/temp' + str(i) + '.txt')
        for line in f:
            tab = line.find('\t')
            did = int(line[:tab])
            allLines[line] = did

    sorted_x = sorted(allLines.items(), key=operator.itemgetter(1))
    g = open('tmp/temp.txt', 'w')
    for tup in sorted_x:
        g.write(tup[0])
    g.close()



# type file
def type(typeFile):
    # read target types
    f = open(typeFile)
    for line in f:
        myType = line.split('\t')[0]
        if myType != 'NIL':
            typeDict[myType] = set()
            typeDict[myType].add(myType)
    print typeDict
    f.close()
    return 

# Extract dbpedia annotations
def extractAnnotations(docJson):
    validEntities = []
    decoded = json.loads(docJson)
    for entity in decoded['Resources']:
        # isTarget = False
        # types = entity['@types'].split(',')
        # for eType in types:
        #   if eType in typeSet:
        #       isTarget = True
        #       entity['@types'] = eType
        #       break
        isTarget = True
        if isTarget:
            validEntities.append(entity)

    return validEntities

# map dbpedia to freebase
def linkToFreebase(entity):
    dbID = entity['@URI'][28:]
    if dbID in dbpediaToFreebase:
        entity['@URI'] = dbpediaToFreebase[dbID]
    else:
        entity['@URI'] = None


# read the freebase entity and extract the notable type
def findingNotableTypes(freebasekey):
    f = open('tmp/temp.txt')
    idToType = {}
    # Get all the types
    for line in f:
        segments = line.strip('\r\n').split('\t')
        sim_score = float(segments[3])
        rank_score = float(segments[4])
        # if sim_score > 0.1 or rank_score == -1: 
        idToType[segments[2]] = None
    print 'Find notable type, total# entities: ', len(idToType)
    # Get notable type for entities, if don't have notable type, remove it
    index = 0
    for key in idToType:
        index += 1
        if (index % 10000 == 0):
            print index
        try:
            service_url = 'https://www.googleapis.com/freebase/v1/topic'
            topic_id = '/' + key.replace('.', '/')
            params = {
              'key': freebasekey,
              'filter': '/common/topic/notable_types'
            }
            url = service_url + topic_id + '?' + urllib.urlencode(params)
            topic = json.loads(urllib2.urlopen(url, timeout=10).read())
            idToType[key] = topic['property']['/common/topic/notable_types']['values'][0]['id']
        except:
            continue

    g = open('tmp/temp_2.txt', 'w')
    f.close()
    f = open('tmp/temp.txt')
    #print typeDict
    # write down the entites
    for line in f:
        segments = line.strip('\r\n').split('\t')
        g.write(segments[0] + '\t' + segments[1] + '\t' + str(idToType[segments[2]]) + '\t' + segments[2]
         + '\t' + segments[3] + '\t' + segments[4] + '\n')
    g.close()



def filterTypes(typeFile, outFile, freebasekey):
    print 'Filter not-of-interested entities'
    f = open('tmp/temp_2.txt')
    g = open(outFile, 'w')
    typeF = open(typeFile)
    for line in typeF:
        myType = line.strip('\r\n').split('\t')[0]
        if myType != 'NIL':
            typeDict[myType] = set()
            typeDict[myType].add(myType)
    index = 0
    for line in f:
        index += 1
        if index % 10000 == 0:
            print index
        segments = line.strip('\r\n').split('\t')
        myType = segments[2]
        filteredTypes = exploreType(myType, freebasekey)
        filteredTypesStr = ''
        for temp in filteredTypes:
            filteredTypesStr += temp + ';'
        g.write(segments[0] + '\t' + segments[1] + '\t' + segments[2] + '\t' + filteredTypesStr + '\t' + segments[3]
         + '\t' + segments[4] + '\t' + segments[5] + '\n')
    g.close()
        


# explore the ancestors of a given type
def exploreType(my_type, freebasekey):
    if my_type == '/common/topic':
        return None
    #print my_type
    if my_type not in typeDict:
        try:
            typeDict[my_type] = set()
            service_url = 'https://www.googleapis.com/freebase/v1/topic'
            topic_id = my_type
            params = {
              'key': freebasekey,
              'filter': '/freebase/type_hints/included_types'
            }
            url = service_url + topic_id + '?' + urllib.urlencode(params)
            topic = json.loads(urllib2.urlopen(url, timeout=10).read())
            for father in topic['property']['/freebase/type_hints/included_types']['values']:
                fatherID = father['id']
                filtered = exploreType(fatherID)
                if (filtered != None):
                    for temp in filtered:
                        typeDict[my_type].add(temp)
        except:
            return typeDict[my_type]

    return typeDict[my_type]


if __name__ == "__main__":
    inFileName='../'+sys.argv[1] # RawText
    typeFile='../'+sys.argv[2]
    mapFile='../'+sys.argv[3] # ../data/freebase_links.nt
    outFile='../'+sys.argv[4]
    freebasekey=sys.argv[5]
    mapping(mapFile)
    link(inFileName, 0.2) # DBpediaSpotlight
    findingNotableTypes(freebasekey) # find notable type for each entity
    filterTypes(typeFile, outFile, freebasekey) # filter types