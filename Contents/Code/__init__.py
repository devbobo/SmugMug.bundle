import re

SMUGMUG_URL = 'http://api.smugmug.com'
SMUGMUG_API_URI = '/api/v2'
SMUGMUG_USER_URI = '%s%%s/user/%%%%s' % SMUGMUG_URL % SMUGMUG_API_URI
SMUGMUG_FOLDER_URI = '%s%%s/folder/user/%%%%s%%%%%%%%s' % SMUGMUG_URL % SMUGMUG_API_URI
SMUGMUG_ALBUM_URI = '%s%%s/album/%%%%s'% SMUGMUG_URL % SMUGMUG_API_URI

####################################################################################################
def Start():
    ObjectContainer.title1 = 'SmugMug'
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:15.0) Gecko/20100101 Firefox/15.0.1'

####################################################################################################
@handler('/photos/smugmug', 'SmugMug')
def MainMenu():
    
    oc = ObjectContainer()
    
    accounts = Data.LoadObject('Accounts') if Data.Exists('Accounts') else []
    
    for account in accounts:
        uri = SMUGMUG_USER_URI % account
        
        try:
            data = Get(uri, {"_shorturis": "", "_filteruri": "BioImage", "_filter": "Name,NickName", "_expand": "BioImage%3F_shorturis%3D%26_filter%3D%26_filteruri%3DImageSizes,BioImage.ImageSizes%3F_filteruri%3D%26_filter%3DMediumImageUrl"})
        except:
            data = Get(uri, {"_filteruri": "", "_filter": "Name,NickName"})
        
        user = getObjectByLocator(data)

        uris = None
        
        if ("Uris" in user and "BioImage" in user["Uris"]):
            uris = getExpansionFromObject(data, getExpansionByLocator(data, user["Uris"]["BioImage"]), "ImageSizes")
        
        oc.add(
            DirectoryObject(
                key     = Callback(GetFolder, nickname=user["NickName"]),
                title   = user["Name"],
                thumb   = uris["MediumImageUrl"] if uris != None and "MediumImageUrl" in uris else ""
            )
        )
    
    oc.add(
        InputDirectoryObject(
            key     = Callback(AddAccount),
            title   = L('Add Account...'),
            prompt  = L('Enter SmugMug NickName')
        )
    )

    return oc

####################################################################################################
@route('/photos/smugmug/user/{nickname}')
@route('/photos/smugmug/user/{nickname}/{urlPath}')
def GetFolder(nickname, urlPath=""):

    oc = ObjectContainer()
    
    uri = SMUGMUG_FOLDER_URI % nickname % ("/" + urlPath if urlPath != "" else "")

    try:
        data = Get(uri, {"_shorturis": "", "_filteruri": "Folders,FolderAlbums", "_expand": "Folders%3F_shorturis%3D%26_filter%3DName%2CUrlPath%26_filteruri%3DFolderHighlightImage,Folders.FolderHighlightImage%3F_shorturis%3D%26_filter%3D%26_filteruri%3DImageSizes,Folders.FolderHighlightImage.ImageSizes%3F_filteruri%3D%26_filter%3DMediumImageUrl,FolderAlbums%3F_shorturis%3D%26_filter%3DTitle%2CDescription%2CUri%26_filteruri%3DAlbumHighlightImage,FolderAlbums.AlbumHighlightImage%3F_shorturis%3D%26_filter%3D%26_filteruri%3DImageSizes,FolderAlbums.AlbumHighlightImage.ImageSizes%3F_filteruri%3D%26_filter%3DMediumImageUrl"})
    except:
        data = None

    root = getObjectByLocator(data)

    if (root != None and "Name" in root and root["Name"] != ""):
        oc.title1 = root["Name"]

    folders = getExpansionFromObjectByLocator(data, "Folders", [])
    
    for folder in folders:
        uris = None
        
        if ("Uris" in folder and "FolderHighlightImage" in folder["Uris"]):
            uris = getExpansionFromObject(data, getExpansionByLocator(data, folder["Uris"]["FolderHighlightImage"]), "ImageSizes")
        
        oc.add(
            DirectoryObject(
                key     = Callback(GetFolder, nickname=nickname, urlPath=folder["UrlPath"][1:]),
                title   = folder["Name"],
                thumb   = uris["MediumImageUrl"] if uris != None and "MediumImageUrl" in uris else ""
            )
        )
    
    albums = getExpansionFromObjectByLocator(data, "FolderAlbums", [])

    for album in albums:
        uris = None
        
        if ("Uris" in album and "AlbumHighlightImage" in album["Uris"]):
            uris = getExpansionFromObject(data, getExpansionByLocator(data, album["Uris"]["AlbumHighlightImage"]), "ImageSizes")
        
        albumUri = album["Uri"][7:]
        oc.add(
            PhotoAlbumObject(
                key         = Callback(GetAlbum, id=re.sub('.+\/', '', albumUri)),
                rating_key  = albumUri,
                title       = album["Title"],
                summary     = album["Description"],
                thumb       = uris["MediumImageUrl"] if uris != None and "MediumImageUrl" in uris else ""
            )
        )

    oc.objects.sort(key = lambda obj: obj.title)

    return oc

####################################################################################################
@route('/photos/smugmug/album/{id}')
def GetAlbum(id):
    oc = ObjectContainer()

    data = Get(SMUGMUG_ALBUM_URI % id, {"_shorturis": "", "_filteruri": "AlbumImages","_filter": "Title,Uri",  "_expand": "AlbumImages%3F_shorturis%3D%26_filteruri%3DImageSizes%26_filter%3DCaption%2CTitle,AlbumImages.ImageSizes%3F_shorturis%3D%26_filteruri%3D%26_filter%3D%20MediumImageUrl%2C%20LargestImageUrl"})
    #http://api.smugmug.com/api/v2/album/9HbmnZ?_pretty=&_expand=AlbumImages%3F_shorturis%3D%26_filteruri%3DImageSizes%26_filter%3DCaption%2CTitle,AlbumImages.ImageSizes%3F_shorturis%3D%26_filteruri%3D%26_filter%3D%20MediumImageUrl%2C%20LargestImageUrl&_filter=Title,Uri&_shorturis=&_filteruri=AlbumImages&_accept=application/json

    album = getObjectByLocator(data)
    
    if (album != None and "Title" in album and album["Title"] != ""):
        oc.title1 = album["Title"]
    
    photos = getExpansionFromObjectByLocator(data, "AlbumImages", [])
    
    for photo in photos:
        if ("Uris" in photo and "ImageSizes" in photo["Uris"]):
            uris = getExpansionFromObject(data, photo, "ImageSizes")
        
        oc.add(
            PhotoObject(
                thumb   = uris["MediumImageUrl"] if uris != None and "MediumImageUrl" in uris else "",
                title   = photo["Title"],
                summary = photo["Caption"],
                url     = uris["LargestImageUrl"] if uris != None and "LargestImageUrl" in uris else ""
            )
        )

    return oc

####################################################################################################
def AddAccount(query):
    accounts = Data.LoadObject('Accounts') if Data.Exists('Accounts') else []
    
    uri = SMUGMUG_USER_URI % query
    
    data = Get(uri, {"_shorturis": "", "_filteruri": ""})
    user = getObjectByLocator(data)
    
    if user == None:
        return MessageContainer(L("Not Found"), L("Invalid user"))
    
    accounts.append(query)
    Data.SaveObject('Accounts', accounts)

    return MainMenu

####################################################################################################
def Get(uri, params={}):
    
    params = params if params != None else {}
    
    params["_pretty"] = ""
    
    query = "?"
    
    for key in params:
        query += key + "=" + params[key] + "&"

    json = JSON.ObjectFromURL(uri + query)

    return json

####################################################################################################
def getExpansionByLocator(data, key, overrideObject=None):

    if data == None or not("Expansions" in data) or key == None:
        return overrideObject

    expansion = data["Expansions"][key] if key in data["Expansions"] else None
    
    if expansion == None:
        return overrideObject
    
    locator = expansion["Locator"]
    defaultObject = [] if "LocatorType" in expansion and expansion["LocatorType"] == 'Objects' else overrideObject
    
    return expansion[locator] if locator in expansion else defaultObject

####################################################################################################
def getExpansionFromObject(data, object, key, overrideObject=None):
    index = object["Uris"][key] if object != None and "Uris" in object and key in object["Uris"] else None
    item = getExpansionByLocator(data, index, overrideObject)
    
    return item

####################################################################################################
def getExpansionFromObjectByLocator(data, key, overrideObject=None):
    
    object = getObjectByLocator(data)
    item = getExpansionFromObject(data, object, key, overrideObject)

    return item

####################################################################################################
def getObjectByLocator(data, overrideObject=None):

    if data == None or not "Response" in data:
        return overrideObject
    
    locator = data["Response"]["Locator"]
    defaultObject = {} if "LocatorType" in data["Response"] and data["Response"]["LocatorType"] == 'Objects' else overrideObject
    
    return data["Response"][locator] if locator in data["Response"] else defaultObject


