__author__ = 'xiang'
import sys

if __name__ == "__main__":
	path = '../' + sys.argv[1]
	Documents = []
	flag = False
	with open(path,'r') as f:
		for line in f:
			line = line.strip()
			if line:
				# print line
				Documents.append(line)
				if not line.split('\t')[0].isdigit():
					flag = True

	if flag:
		print "Add DocId for input file..."
		docId = 0
		with open(path, 'w') as f:
			for line in Documents:
				f.write(str(docId) + '\t' + line + '\n')
				docId = docId + 1
