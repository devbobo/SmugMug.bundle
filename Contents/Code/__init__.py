import re

SMUGMUG_PREFIX = '/photos/smugmug'
SMUGMUG_URL = 'http://api.smugmug.com'
SMUGMUG_API_URI = '/api/v2'
SMUGMUG_USER_URL = '%s%%s/user/%%%%s' % SMUGMUG_URL % SMUGMUG_API_URI
SMUGMUG_FOLDER_URL = '%s%%s/folder/user/%%%%s%%%%%%%%s' % SMUGMUG_URL % SMUGMUG_API_URI
SMUGMUG_ALBUM_URL = '%s%%s/album/%%%%s'% SMUGMUG_URL % SMUGMUG_API_URI
SMUGMUG_FEATURED_URL = '%s!featuredalbums' % SMUGMUG_USER_URL
SMUGMUG_POPULAR_URL = '%s!popularmedia' % SMUGMUG_USER_URL

SMUGMUG_USER_URI = '/user/%s'
SMUGMUG_ALBUM_URI = '/album/%s'
SMUGMUG_FEATURED_URI = '%s/featured' % SMUGMUG_USER_URI
SMUGMUG_POPULAR_URI = '%s/popular' % SMUGMUG_USER_URI

####################################################################################################
def Start():
    ObjectContainer.title1 = 'SmugMug'
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:15.0) Gecko/20100101 Firefox/15.0.1'

####################################################################################################
@handler(SMUGMUG_PREFIX, 'SmugMug')
def MainMenu():
    
    oc = ObjectContainer()
    
    accounts = Data.LoadObject('Accounts') if Data.Exists('Accounts') else []
    
    for account in accounts:
        uri = SMUGMUG_USER_URL % account
        
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
                key     = Callback(GetUser, nickname=user["NickName"]),
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
@route(SMUGMUG_PREFIX + SMUGMUG_USER_URI % '{nickname}')
def GetUser(nickname):

    oc = ObjectContainer()
    
    uri = SMUGMUG_USER_URL % nickname
    
    try:
        data = Get(uri, {"_filteruri": "", "_filter": "Name,NickName"})
    except:
        data = None
    
    user = getObjectByLocator(data)

    oc.title1 = user["Name"]

    oc.add(
        DirectoryObject(
            key     = Callback(GetFolder, nickname=user["NickName"]),
            title   = L("Galleries")
        )
    )

    oc.add(
       DirectoryObject(
            key     = Callback(GetFeatured, nickname=user["NickName"]),
            title   = L("Featured")
        )
    )

    oc.add(
        PhotoAlbumObject(
            key         = Callback(GetPopular, nickname=user["NickName"]),
            rating_key  = SMUGMUG_PREFIX + SMUGMUG_POPULAR_URI % user["NickName"],
            title       = L("Popular"),
        )
   )

    return oc


####################################################################################################
@route(SMUGMUG_PREFIX + SMUGMUG_USER_URI % '{nickname}' + '/gallery')
@route(SMUGMUG_PREFIX + SMUGMUG_USER_URI % '{nickname}' + '/gallery/{urlPath}')
def GetFolder(nickname, urlPath=""):

    oc = ObjectContainer(title1="Galleries")

    uri = SMUGMUG_FOLDER_URL % nickname % ("/" + urlPath if urlPath != "" else "")

    try:
        data = Get(uri, {"_shorturis": "", "_filteruri": "Folders,FolderAlbums", "_expand": "Folders%3F_shorturis%3D%26_filter%3DName%2CUrlPath%26_filteruri%3DFolderHighlightImage,Folders.FolderHighlightImage%3F_shorturis%3D%26_filter%3D%26_filteruri%3DImageSizes,Folders.FolderHighlightImage.ImageSizes%3F_filteruri%3D%26_filter%3DMediumImageUrl,FolderAlbums%3F_shorturis%3D%26_filter%3DTitle%2CDescription%2CUri%26_filteruri%3DAlbumHighlightImage,FolderAlbums.AlbumHighlightImage%3F_shorturis%3D%26_filter%3D%26_filteruri%3DImageSizes,FolderAlbums.AlbumHighlightImage.ImageSizes%3F_filteruri%3D%26_filter%3DMediumImageUrl"})
    except:
        data = None

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

    iterateAlbums(oc, data, getExpansionFromObjectByLocator(data, "FolderAlbums", []))

    return oc

####################################################################################################
@route(SMUGMUG_PREFIX + SMUGMUG_FEATURED_URI % '{nickname}')
def GetFeatured(nickname):
    
    oc = ObjectContainer(title1="Featured")

    uri = SMUGMUG_FEATURED_URL % nickname

    try:
        data = Get(uri, {"_shorturis": "", "_filter": "Title,Description,Uri", "_filteruri": "AlbumHighlightImage", "_expand": "AlbumHighlightImage&_expand=AlbumHighlightImage%3F_shorturis%3D%26_filteruri%3DImageSizes%26_filter%3D,AlbumHighlightImage.ImageSizes%3F_filteruri%3D%26_filter%3DMediumImageUrl"})
    except:
        data = None

    return iterateAlbums(oc, data, getObjectByLocator(data, []))

####################################################################################################
@route(SMUGMUG_PREFIX + SMUGMUG_ALBUM_URI % '{id}')
def GetAlbum(id):
    oc = ObjectContainer()

    data = Get(SMUGMUG_ALBUM_URL % id, {"_shorturis": "", "_filteruri": "AlbumImages","_filter": "Title,Uri",  "_expand": "AlbumImages%3F_shorturis%3D%26_filteruri%3DImageSizes%26_filter%3DCaption%2CTitle,AlbumImages.ImageSizes%3F_shorturis%3D%26_filteruri%3D%26_filter%3D%20MediumImageUrl%2CLargestImageUrl"})

    album = getObjectByLocator(data)
    
    if (album != None and "Title" in album and album["Title"] != ""):
        oc.title1 = album["Title"]
    
    return iterateImages(oc, data, getExpansionFromObjectByLocator(data, "AlbumImages", []))

####################################################################################################
@route(SMUGMUG_PREFIX + SMUGMUG_POPULAR_URI % '{nickname}')
def GetPopular(nickname):
    
    oc = ObjectContainer(title1="Popular")
    
    uri = SMUGMUG_POPULAR_URL % nickname
    
    try:
        data = Get(uri, {"_shorturis": "", "_filter": "Caption,Title", "_filteruri": "ImageSizes", "_expand": "ImageSizes%3F_filteruri%3D%26_filter%3DMediumImageUrl%2CLargestImageUrl"})
    except:
        data = None
    
    return iterateImages(oc, data, getObjectByLocator(data, []))

####################################################################################################
def AddAccount(query):
    accounts = Data.LoadObject('Accounts') if Data.Exists('Accounts') else []
    
    uri = SMUGMUG_USER_URL % query
    
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
def iterateAlbums(oc, data, albums):

    for album in albums:
        uris = None

        if ("Uris" in album and "AlbumHighlightImage" in album["Uris"]):
            uris = getExpansionFromObject(data, getExpansionByLocator(data, album["Uris"]["AlbumHighlightImage"]), "ImageSizes")

        albumUri = album["Uri"][7:]

        oc.add(
            PhotoAlbumObject(
                key         = Callback(GetAlbum, id=re.sub('.+\/', '', albumUri)),
                rating_key  = SMUGMUG_PREFIX + albumUri,
                title       = album["Title"],
                summary     = album["Description"],
                thumb       = uris["MediumImageUrl"] if uris != None and "MediumImageUrl" in uris else ""
            )
        )

    oc.objects.sort(key = lambda obj: obj.title)

    return oc

####################################################################################################
def iterateImages(oc, data, images):
    for image in images:
        if ("Uris" in image and "ImageSizes" in image["Uris"]):
            uris = getExpansionFromObject(data, image, "ImageSizes")
        
        oc.add(
           PhotoObject(
               thumb   = uris["MediumImageUrl"] if uris != None and "MediumImageUrl" in uris else "",
               title   = image["Title"],
               summary = image["Caption"],
               url     = uris["LargestImageUrl"] if uris != None and "LargestImageUrl" in uris else ""
               )
           )

    return oc

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


