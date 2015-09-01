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
typeDict = []
docList = {}
dbpediaToFreebase = {}
threadNum = 1
maxDid = 0

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
            if int(did) <= maxDid:
                if did in self.docList:
                    try:
                        doc = self.docList[did]
                        url = "http://spotlight.dbpedia.org/rest/annotate"
                        #url = "http://localhost:2222/rest/annotate"
                        data = {"confidence":self.confidence}
                        data["support"] = "20"
                        data["text"] = doc;
                        data = urllib.urlencode(data)
                        req = urllib2.Request(url)
                        req.add_header('Accept', 'application/json') #text/xml')
                        print did
                        page = html.fromstring(urllib2.urlopen(req, data, timeout=100).read())
                        docJson = html.tostring(page)[3:-4]
                        validEntities = extractAnnotations(docJson)
                        for entity in validEntities:
                            linkToFreebase(entity)
                            types = extractTypes(entity['@types'])
                            typeStr = ''
                            for temp in types:
                                typeStr += temp + ';'
                            if (entity['@URI'] != None):
                                if len(types) == 1:
                                    g.write(str(index + self.offset) + '\t' + entity['@surfaceForm'] + '\t' + typeStr + '\t' + typeStr[:-1] + '\t' + entity['@URI'] + '\t' + entity['@similarityScore'] + '\t' + entity['@percentageOfSecondRank'] + '\n')
                                elif len(types) > 1:
                                    g.write(str(index + self.offset) + '\t' + entity['@surfaceForm'] + '\t' + typeStr + '\t' + '' + '\t' + entity['@URI'] + '\t' + entity['@similarityScore'] + '\t' + entity['@percentageOfSecondRank'] + '\n')
                        index += threadNum
                    except:
                        index += threadNum
                        print 'noresult'
                else:
                    index += threadNum
                    continue
            else:
                break
        g.close()


def link(docFile, outFile, confidence):
    # read documents
    global maxDid
    f = open(docFile)
    for doc in f:
        tab = doc.find('\t')
        did = doc[:tab]
        text = doc[tab+1:]
        docList[did] = text
        if maxDid < int(did):
            maxDid = int(did)
    f.close()

    print 'Document #:', len(docList)
    print 'Max document id:', maxDid

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
    g = open(outFile, 'w')
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
            typeDict.append(myType)
    print typeDict
    f.close()
    return

# extract dbpedia annotations
def extractAnnotations(docJson):
    validEntities = []
    decoded = json.loads(docJson)
    for entity in decoded['Resources']:
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

# extract types
def extractTypes(typeStr):
    types = typeStr.split(',')
    myTypes = set()
    for t in types:
        if t[9:] in typeDict:
            myTypes.add(t[9:])
    return myTypes

if __name__ == "__main__":
    inFileName='../'+sys.argv[1] # RawText
    typeFile='../'+sys.argv[2]
    mapFile='../'+sys.argv[3] # ../data/freebase_links.nt
    outFile='../'+sys.argv[4]
    mapping(mapFile)
    type(typeFile)
    link(inFileName, outFile, 0.2) # DBpediaSpotlight