#! python
# GIFmaker.py - easy automatically creating GIFs from captures (name is a WIP)
# I really can't think of a better name

# This is my first project with working with an API so I have no idea what I'm doing

# Just some normal imports
import os, re, logging, json, time, shutil

# This is because I think requests is too hard to type
import requests as req

logging.disable()
# For debug text (only used while making the program of course) (reminder to self: turn off when you're done)
logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')

# The regex for finding the date in the name (based on standard 'Windows Gamebar' file naming)
# 1-2: month, 3-4: day, 5: year, 6-7: hour, 8-9: minute, 10-11: seconds, 12: am/pm
dateRegex = re.compile(r'(\d)?(\d)_(\d)?(\d)_(\d\d\d\d)\s(\d)?(\d)_(\d)?(\d)_(\d)?(\d)\s(A?P?)')
# This variable is to seperate the normal groups from the groups that are optional in the regex
optionalGroups = [1, 3, 6, 8, 10]

# Standard name for the file where it will save the gfys
gfyUrlName = 'gfyUrl.txt'    
# This is the standard folder for 'Windows Gamebar' captures
capturesFolder = os.path.join(os.environ['HOMEPATH'], r'Videos\Captures')
# The folder for the archived captures
capturesArchiveFolder = os.path.join(os.environ['HOMEPATH'], r'Videos\Archive')
# This is the folder where the program itself is located
# If you want the .txt file with the URLs to be dropped somewhere else, 
# change the below variable to the path of the desired destination
programFolder = os.getcwd()

# Where to request a token
tokenUrl = 'https://api.gfycat.com/v1/oauth/token'
# This is the url where you need to request some info from the GfyCat API
requestUrl = 'https://api.gfycat.com/v1/gfycats'
# URL where to upload video
uploadUrl = 'https://filedrop.gfycat.com/'
# The URL for checking the upload status
checkUrl = 'https://api.gfycat.com/v1/gfycats/fetch/status/{}'
# URL for what your GfyCat URL is going to be
gfyUrl = 'https://gfycat.com/{}'


# Format for the text file
gfyUrlText = "Video: {}\nURL: https://gfycat.com/{}\n\n"

bodyTemplate = {
    "grant_type": "password",
    "client_id": "<CLIENT ID HERE>",
    "client_secret": "<CLIENT SECRET HERE>",
    "username": "<USERNAME HERE>",
    "password": "<PASSWORD HERE>"
}

# Create body.json if there is no body.json
try:
    with open('body.json') as body_file:
        body = json.load(body_file)
except:
    with open('body.json', 'w') as body_file:
        json.dump(bodyTemplate, body_file)
    print("'body.json' was just created, \nopen the file and write your personal data inside.")
    input("Press 'enter' to quit...")
    exit()

# The parameters of the GIF
gifParam = {
    "title": "Look at this clip that is probably something cool",
    "description": "I wouldn't know because this GIF is automatically generated..",
    "private": True,
    "noMd5": True
    }

def main():
    videoName = getVid()
    if videoName != "Nothing":
        auth_headers = authHeaders()
    
        gfyID = getUrl(auth_headers)

        uploadFile(gfyID, videoName)

        writeFile(gfyID, videoName)

        movetoArchive(videoName)

# Get video latest from capturesFolder
# Latest video based on standard 'Windows Gamebar' file naming
def getVid():
    # Declaring the variables used in this function
    fileMatch = []
    fileDate = []
    fileLookup = {}
    
    fileHighest = 0
    
    # Change the current working directory to the capturesFolder, 
    # but if you couldn't guess that I don't know what you're doing here    
    os.chdir(capturesFolder)

    # Walk (or run, that's based on your computer speed lmao) through the capturesFolder to find all the captures
    # There are no folders in the capturesFolder so I haven't done anything to work with folders whoops
    for foldername, subfolder, filenames in os.walk(capturesFolder):
        # Loop through all of the files in the filenames variable
        for i in range (len(filenames)):
            optionalGroupsTEMP = []

            # More debug stuff, ignore pls
            logging.debug("File currently working on: " + filenames[i])

            # Search the filename (of this loop) for the right date specification (see where I declared the regex)
            fileMatch.append(dateRegex.search(filenames[i]))

            # Only do something if the regex actually found something
            if fileMatch[i] != None:
                for j in range(len(optionalGroups)):
                    # If the optional group didn't find anything, it gets set to 0
                    if fileMatch[i].group(optionalGroups[j]) == None:
                        optionalGroupsTEMP.append('0')
                    # Else set it to the value it found
                    else:
                        optionalGroupsTEMP.append(fileMatch[i].group(optionalGroups[j]))

                # If it ends with AM set it to 0
                if fileMatch[i].group(12) == 'A':
                    optionalGroupsTEMP.append('0')
                # PM becomes 1
                elif fileMatch[i].group(12) == 'P':
                    optionalGroupsTEMP.append('1')

                # Create a large number of the date it found
                # Format is yyyy mm dd a/p hh mm ss
                # (so '31_12_2018 11_3_42 PM' becomes '201812311110342')
                fileDate.append(int(fileMatch[i].group(5) + optionalGroupsTEMP[0] + fileMatch[i].group(2) + optionalGroupsTEMP[1] + fileMatch[i].group(4) + optionalGroupsTEMP[5] + fileMatch[i].group(7) + optionalGroupsTEMP[3] + fileMatch[i].group(9) + optionalGroupsTEMP[4] + fileMatch[i].group(11)))

                # Assign the large date number to a dictonairy,
                # so we can easily look up what filename belongs to what date
                fileLookup[fileDate[i]] = filenames[i]

                # If the previously biggest number (highest date) is smaller than the date we just generated,
                # replace it with the new number
                if fileHighest < fileDate[i]:
                    fileHighest = fileDate[i]
            
            # This is so that the amount of things in fileDate stays matched up with fileHighest
            else:
                fileDate.append(None)
    
    # Debugging, if you're reading this you haven't learned from the previous debugging code comment i made ;D
    logging.debug("Highest reached number: " + str(fileHighest))
    logging.debug("File that belongs to that number: " + fileLookup[fileHighest])

    if fileLookup[fileHighest] == None:
        return "Nothing"
    else:
        # Returning the filename of with the highest date
        return fileLookup[fileHighest]

# Create auth header
def authHeaders():
    # Get a token
    token = req.post(tokenUrl, json=body)
    access_token = token.json().get("access_token")

    logging.debug("access_token: " + access_token)

    # Idk the reference did this
    auth_headers = {
        "Authorization": "Bearer {}".format(access_token)
    }

    return auth_headers

# Get custom url from GfyCat
def getUrl(headers):
    # Ask GfyCat for an URL
    gfyReturn = req.post(requestUrl, json=gifParam, headers=headers)
    # Get the name out of the data it sends
    gfyID = gfyReturn.json().get("gfyname")

    # Just ignore this again
    logging.debug("gfyID: " + gfyID)

    return gfyID

# Upload file to GfyCat
def uploadFile(gfyID, videoName):
    uploadStatus = "encoding"
    
    # Open the video and write it to a dict
    # These 6 lines took me 5 days because of the (lack of) API documentation
    with open(videoName, 'rb') as payload:
        files = {
            'key': gfyID,
            'file': (videoName, payload),
        }
        res = req.post(uploadUrl, files=files)

    # Ignore pls
    logging.debug(res.text)

    while uploadStatus != "complete":
        checkReturn = req.get(checkUrl.format(gfyID))
        uploadStatus = checkReturn.json().get("task")

        # You know what to do
        logging.debug("Status: " + uploadStatus)
        time.sleep(5)

# Write URL to text document
def writeFile(gfyID, videoName):
    os.chdir(programFolder)

    with open(gfyUrlName, 'a+') as f:
        f.write(gfyUrlText.format(videoName, gfyID))

# Move old capture files to the archive        
def movetoArchive(videoName):
    os.chdir(capturesFolder)

    if os.path.exists(capturesArchiveFolder) == False:
        os.mkdir(capturesArchiveFolder)

    shutil.move(videoName, capturesArchiveFolder)

# This is so it starts with 'main()' when you run it
if __name__ == "__main__":
    main()