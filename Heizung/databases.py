import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

from requests import post


# Firebase
PRIMARY_KEY_FILE="schallebergfarm-firebase-adminsdk-fbsvc-fe101a4402.json"
DATABASE_URL = 'https://schallebergfarm-default-rtdb.europe-west1.firebasedatabase.app'



#initialize firebase
# Fetch the service account key JSON file contents
cred = credentials.Certificate(PRIMARY_KEY_FILE)

# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    'databaseURL': DATABASE_URL
})
    


def sendToVolkszaehler(host, channelId, value, description):
    try:
        resp = post("http://%s/middleware/data/%s.json" %(host, channelId), data={"value" : value})
        print("%s: Response from %s: " % (description, host) + str(resp))
    except Exception as e:
        print("Send to %s failed" %(description) + "Exception:" + str(e))
        
        
def sendToFirebase(variableName, value, description):
    try:
        ref = db.reference(variableName)
        ref.set(value)
    except Exception as e:
        print("Write to firebase realtime database failed" %(description) + "Exception:" + str(e))

