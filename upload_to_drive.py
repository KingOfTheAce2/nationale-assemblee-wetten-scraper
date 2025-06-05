from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

gauth = GoogleAuth()
gauth.LocalWebserverAuth()

drive = GoogleDrive(gauth)

file = drive.CreateFile({'title': 'clean_pdfs.zip'})
file.SetContentFile('clean_pdfs.zip')
file.Upload()

file.InsertPermission({
    'type': 'anyone',
    'value': 'anyone',
    'role': 'reader'
})

print("✅ File uploaded")
print("🔗 Download URL:", file['alternateLink'])
