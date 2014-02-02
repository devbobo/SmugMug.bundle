import re

SMUGMUG_URL = 'http://api.smugmug.com'
SMUGMUG_API_URI = '/api/v2'
SMUGMUG_USER_URI = '%s%%s/user/%%%%s' % SMUGMUG_URL % SMUGMUG_API_URI
SMUGMUG_FOLDER_URI = '%s%%s/folder/user/%%%%s%%%%%%%%s' % SMUGMUG_URL % SMUGMUG_API_URI
SMUGMUG_ALBUM_URI = '%s%%s/album/%%%%s!images'% SMUGMUG_URL % SMUGMUG_API_URI

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
        
        data = Get(uri, {"_shorturis": "", "_filteruri": "BioImage", "_filter": "Name,NickName", "_expand": "BioImage%3F_shorturis%3D%26_filter%3D%26_filteruri%3DImageSizes,BioImage.ImageSizes%3F_filteruri%3D%26_filter%3DMediumImageUrl"})
        
        user = getObjectByLocator(data)
        uris = getExpansionFromObject(data, getExpansionByLocator(data, user["Uris"]["BioImage"]), "ImageSizes")
        
        oc.add(
            DirectoryObject(
				key		= Callback(GetFolder, nickname=user["NickName"]),
				title	= user["Name"],
                thumb   = uris["MediumImageUrl"] if uris != None and uris["MediumImageUrl"] != None else ""
            )
        )
    
    oc.add(
        InputDirectoryObject(
            key		= Callback(AddAccount),
            title	= L('Add Account...'),
            prompt	= L('Enter SmugMug NickName')
        )
    )

    return oc

####################################################################################################
def GetFolder(nickname, path=""):

    oc = ObjectContainer()
    
    uri = SMUGMUG_FOLDER_URI % nickname % path

    data = Get(uri, {"_shorturis": "", "_filteruri": "Folders,FolderAlbums", "_expand": "Folders%3F_shorturis%3D%26_filter%3DName%2CUrlPath%26_filteruri%3DFolderHighlightImage,Folders.FolderHighlightImage%3F_shorturis%3D%26_filter%3D%26_filteruri%3DImageSizes,Folders.FolderHighlightImage.ImageSizes%3F_filteruri%3D%26_filter%3DMediumImageUrl,FolderAlbums%3F_shorturis%3D%26_filter%3DTitle%2CDescription%2CUri%26_filteruri%3DAlbumHighlightImage,FolderAlbums.AlbumHighlightImage%3F_shorturis%3D%26_filter%3D%26_filteruri%3DImageSizes,FolderAlbums.AlbumHighlightImage.ImageSizes%3F_filteruri%3D%26_filter%3DMediumImageUrl", })

    folders = getExpansionFromObjectByLocator(data, "Folders")
    
    for folder in folders:
        uris = getExpansionFromObject(data, getExpansionByLocator(data, folder["Uris"]["FolderHighlightImage"]), "ImageSizes")
        oc.add(
            DirectoryObject(
                key		= Callback(GetFolder, nickname=nickname, path=folder["UrlPath"]),
                title	= folder["Name"],
                thumb   = uris["MediumImageUrl"] if uris != None and uris["MediumImageUrl"] != None else ""
            )
        )
    
    albums = getExpansionFromObjectByLocator(data, "FolderAlbums")
    albums = albums if albums != None else {}

    for album in albums:
        uris = getExpansionFromObject(data, getExpansionByLocator(data, album["Uris"]["AlbumHighlightImage"]), "ImageSizes")
        oc.add(
            PhotoAlbumObject(
                key		= Callback(GetPhotos, id=re.sub('.+\/', '', album["Uri"])),
                rating_key = album["Uri"],
                title	= album["Title"],
                summary = album["Description"],
                thumb   = uris["MediumImageUrl"] if uris != None and uris["MediumImageUrl"] != None else ""
            )
        )

    oc.objects.sort(key = lambda obj: obj.title)

    return oc

####################################################################################################
@route('/photos/smugmug/api/v2/album/{id}')
def GetPhotos(id):
    oc = ObjectContainer()

    data = Get(SMUGMUG_ALBUM_URI % id, {"_shorturis": "", "_expand": "ImageSizes%3F_shorturis%3D%26_filteruri%3D%26_filter%3D%20MediumImageUrl%2C%20LargestImageUrl"})

    photos = getObjectByLocator(data)
    
    for photo in photos:
        uris = getExpansionFromObject(data, photo, "ImageSizes")
        oc.add(
            PhotoObject(
                thumb = uris["MediumImageUrl"],
                title = photo["Title"],
                summary = photo["Caption"],
                url = uris["LargestImageUrl"]
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
def getExpansionByLocator(data, key):

    if data == None or not("Expansions" in data) or key == None:
        return None

    expansion = data["Expansions"][key] if key in data["Expansions"] else None
    
    if expansion == None:
        return None
    
    locator = expansion["Locator"]
    defaultObject = {} if "LocatorType" in expansion and expansion["LocatorType"] == 'Objects' else None
    
    return expansion[locator] if locator in expansion else defaultObject

####################################################################################################
def getExpansionFromObject(data, object, key):
    index = object["Uris"][key] if object != None and "Uris" in object and key in object["Uris"] else None
    item = getExpansionByLocator(data, index)
    
    return item

####################################################################################################
def getExpansionFromObjectByLocator(data, key):
    
    object = getObjectByLocator(data)
    item = getExpansionFromObject(data, object, key)

    return item

####################################################################################################
def getObjectByLocator(data):

    if data == None or not "Response" in data:
        return None
    
    locator = data["Response"]["Locator"]
    defaultObject = {} if "LocatorType" in data["Response"] and data["Response"]["LocatorType"] == 'Objects' else None
    
    return data["Response"][locator] if locator in data["Response"] else defaultObject


