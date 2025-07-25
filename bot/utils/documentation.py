import os

#Functions for managing the documentation files located in ./documentation/

def getdoc(idx: int = None) -> str:
    #runtime variables
    data = str()

    #flag variables
    fileFound = bool(False)
    fileRead = bool(False)

    if idx == None:
        data = "Commands: \n"
        for i,doc in enumerate(os.listdir("./doc")):
            doc = doc[:-3]  # Strip the .md extension
            data = data + str(i) + ". " + doc + "\n"
            fileFound = True
        
        if fileFound == True:
            return data
        else:
            data = "Sorry, I was unable to find documentation files."
            return data

    else: #return data from file at index
        for i,doc in enumerate(os.listdir("./doc")):
            if str(i+1) == str(idx):
                file = open("./doc/" + doc)
                data = file.read()
                file.close()
                fileRead = True
        
        if fileRead == True:
            return data
        else:
            data = "Sorry, I was not able to read the documentation file or it does not exist."
            return data