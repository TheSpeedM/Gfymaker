#! python
# GIFmaker.py - easy automatically creating GIFs from videos (name is a WIP)
# I really can't think of a better name

# This is my first project with working with an API so I have no idea what I'm doing

# Just some normal imports
import os, re, logging, json, time, shutil, sys

# This is because I think requests is too hard to type
import requests as req

# For debug text (only used while making the program of course) (reminder to self: turn off when you're done)
logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')

# Standard name for the file where it will save the gfys
gfyUrlName = 'gfyUrl.txt'    
# This is the folder where you have your videos
videoFolder = os.path.join(os.environ['HOMEPATH'], r'Videos\Videos')
# The folder for the archived videos
videoArchiveFolder = os.path.join(os.environ['HOMEPATH'], r'Videos\Archive')
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

# Client ID and -Secret should be requested at https://developers.gfycat.com/
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
    if videoName != None:
        auth_headers = authHeaders()
    
        gfyID = getUrl(auth_headers)

        uploadFile(gfyID, videoName)

        writeFile(gfyID, videoName)

        movetoArchive(videoName)
    else:
        sys.exit()

# Get video latest from videoFolder
def getVid():
    videos = os.listdir(videoFolder)
    
    if videos != []:
        return videos[0]
    else:
        return None

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
    # Change the current working directory to the videoFolder, 
    # but if you couldn't guess that I don't know what you're doing here    
    os.chdir(videoFolder)

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

    # Check if it is done uploading
    while uploadStatus != "complete":
        checkReturn = req.get(checkUrl.format(gfyID))
        uploadStatus = checkReturn.json().get("task")

        # You know what to do
        logging.debug("Status: " + uploadStatus)
        time.sleep(5)

# Write URL to text document
def writeFile(gfyID, videoName):
    os.chdir(videoFolder)

    with open(gfyUrlName, 'a+') as f:
        f.write(gfyUrlText.format(videoName, gfyID))

# Move old capture files to the archive
def movetoArchive(videoName):
    os.chdir(videoFolder)

    if os.path.exists(videoArchiveFolder) == False:
        os.mkdir(videoArchiveFolder)

    shutil.move(videoName, videoArchiveFolder)

# This is so it starts with 'main()' when you run it
if __name__ == "__main__":
    main()