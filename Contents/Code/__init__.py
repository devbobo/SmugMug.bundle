import re
from urllib import quote

SMUGMUG_PREFIX = '/photos/smugmug'
SMUGMUG_URL = 'http://api.smugmug.com'
SMUGMUG_API_URI = '/api/v2'

SMUGMUG_FOLDER_URL = '%s%%s/folder/user/%%%%s%%%%%%%%s' % SMUGMUG_URL % SMUGMUG_API_URI
SMUGMUG_ALBUM_URL = '%s%%s/album/%%%%s'% SMUGMUG_URL % SMUGMUG_API_URI

SMUGMUG_USER_URL = '%s%%s/user/%%%%s' % SMUGMUG_URL % SMUGMUG_API_URI
SMUGMUG_USER_FEATURED_URL = '%s!featuredalbums' % SMUGMUG_USER_URL
SMUGMUG_USER_POPULAR_URL = '%s!popularmedia' % SMUGMUG_USER_URL
SMUGMUG_USER_SEARCH_URL = '%s!imagesearch' % SMUGMUG_USER_URL

SMUGMUG_ALBUM_URI = '/album/%s'

SMUGMUG_USER_URI = '/user/%s'
SMUGMUG_USER_FEATURED_URI = '%s/featured' % SMUGMUG_USER_URI
SMUGMUG_USER_POPULAR_URI = '%s/popular' % SMUGMUG_USER_URI
SMUGMUG_USER_SEARCH_URI = '%s/search/%%%%s' % SMUGMUG_USER_URI

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
                thumb   = uris["MediumImageUrl"] if uris != None and "MediumImageUrl" in uris else R("icon-default.png")
            )
        )
    
    oc.add(
        InputDirectoryObject(
            key     = Callback(AddAccount),
            title   = L('Add Account...'),
            prompt  = L('Enter SmugMug NickName'),
            thumb   = R("icon-default.png")
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
            title   = L("Galleries"),
            thumb   = R("icon-default.png")
        )
    )

    oc.add(
       DirectoryObject(
            key     = Callback(GetFeatured, nickname=user["NickName"]),
            title   = L("Featured"),
            thumb   = R("icon-default.png")
        )
    )

    oc.add(
        PhotoAlbumObject(
            key         = Callback(GetPopular, nickname=user["NickName"]),
            rating_key  = SMUGMUG_PREFIX + SMUGMUG_USER_POPULAR_URI % user["NickName"],
            title       = L("Popular"),
            thumb       = R("icon-default.png")
        )
    )

    oc.add(
        InputDirectoryObject(
            key         = Callback(GetUserSearch, nickname=user["NickName"]),
            title       = L("Search"),
            thumb       = R("icon-default.png")
        )
    )

    return oc


####################################################################################################
@route(SMUGMUG_PREFIX + SMUGMUG_USER_URI % '{nickname}' + '/folder')
def GetFolder(nickname, uri=""):

    oc = ObjectContainer(title1=L("Galleries"))

    try:
        data = Get(SMUGMUG_FOLDER_URL % nickname % uri, {"_shorturis": "", "_filteruri": "Folders,FolderAlbums", "_expand": "Folders%3F_shorturis%3D%26_filter%3DName%2CUrlPath%26_filteruri%3DFolderHighlightImage,Folders.FolderHighlightImage%3F_shorturis%3D%26_filter%3D%26_filteruri%3DImageSizes,Folders.FolderHighlightImage.ImageSizes%3F_filteruri%3D%26_filter%3DMediumImageUrl,FolderAlbums%3F_shorturis%3D%26_filter%3DTitle%2CDescription%2CUri%26_filteruri%3DAlbumHighlightImage,FolderAlbums.AlbumHighlightImage%3F_shorturis%3D%26_filter%3D%26_filteruri%3DImageSizes,FolderAlbums.AlbumHighlightImage.ImageSizes%3F_filteruri%3D%26_filter%3DMediumImageUrl"})
    except:
        data = None

    root = getObjectByLocator(data)

    if ("Name" in root and root["Name"] != "Root Node"):
        oc.title1 = root["Name"]

    iterateFolders(oc, data, getExpansionFromObjectByLocator(data, "Folders", []), nickname)
    iterateAlbums(oc, data, getExpansionFromObjectByLocator(data, "FolderAlbums", []))

    return oc

####################################################################################################
@route(SMUGMUG_PREFIX + SMUGMUG_USER_FEATURED_URI % '{nickname}')
def GetFeatured(nickname):
    
    oc = ObjectContainer(title1=L("Featured"))

    uri = SMUGMUG_USER_FEATURED_URL % nickname

    try:
        data = Get(uri, {"_shorturis": "", "_filter": "Title,Description,Uri", "_filteruri": "AlbumHighlightImage", "_expand": "AlbumHighlightImage&_expand=AlbumHighlightImage%3F_shorturis%3D%26_filteruri%3DImageSizes%26_filter%3D,AlbumHighlightImage.ImageSizes%3F_filteruri%3D%26_filter%3DMediumImageUrl"})
    except:
        data = None

    return iterateAlbums(oc, data, getObjectByLocator(data, []))

####################################################################################################
@route(SMUGMUG_PREFIX + SMUGMUG_ALBUM_URI % '{id}')
def GetAlbum(id):
    try:
        data = Get(SMUGMUG_ALBUM_URL % id, {"_shorturis": "", "_filteruri": "AlbumImages","_filter": "Title,Uri",  "_expand": "AlbumImages%3F_shorturis%3D%26_filteruri%3DImageSizes%26_filter%3DCaption%2CTitle,AlbumImages.ImageSizes%3F_shorturis%3D%26_filteruri%3D%26_filter%3D%20MediumImageUrl%2CLargestImageUrl"})
    except:
        data = None

    album = getObjectByLocator(data)

    return iterateImages(ObjectContainer(title1 = album["Title"]), data, getExpansionFromObjectByLocator(data, "AlbumImages", []))

####################################################################################################
@route(SMUGMUG_PREFIX + SMUGMUG_USER_POPULAR_URI % '{nickname}')
def GetPopular(nickname):

    try:
        data = Get(SMUGMUG_USER_POPULAR_URL % nickname, {"_shorturis": "", "_filter": "Caption,Title", "_filteruri": "ImageSizes", "_expand": "ImageSizes%3F_filteruri%3D%26_filter%3DMediumImageUrl%2CLargestImageUrl"})
    except:
        data = None
    
    return iterateImages(ObjectContainer(title1=L("Popular")), data, getObjectByLocator(data, []))

####################################################################################################
@route(SMUGMUG_PREFIX + SMUGMUG_USER_URI % '{nickname}' + '/search')
@route(SMUGMUG_PREFIX + SMUGMUG_USER_SEARCH_URI % '{nickname}' % '{query}')
def GetUserSearch(nickname, query):
    
    try:
        data = Get(SMUGMUG_USER_SEARCH_URL % nickname, {"q": quote(query), "Order": "Newest", "_shorturis": "", "_filter": "Caption,Title", "_filteruri": "ImageSizes", "_expand": "ImageSizes%3F_filteruri%3D%26_filter%3DMediumImageUrl%2CLargestImageUrl"})
    except:
        data = None
    
    return iterateImages(ObjectContainer(title1=L("Search")), data, getObjectByLocator(data, []))

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
    params["APIKey"] = "MxQaTZ58TPeQMZ1VXPpd83HphEtbWPIB"
    
    query = "?"
    
    for key in params:
        query += key + "=" + params[key] + "&"

    return JSON.ObjectFromURL(uri + query)

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
                thumb       = uris["MediumImageUrl"] if uris != None and "MediumImageUrl" in uris else R("icon-default.png")
            )
        )

    oc.objects.sort(key = lambda obj: obj.title)

    return oc

####################################################################################################
def iterateFolders(oc, data, folders, nickname):
    
    folders = getExpansionFromObjectByLocator(data, "Folders", [])
    
    for folder in folders:
        uris = None
        
        if ("Uris" in folder and "FolderHighlightImage" in folder["Uris"]):
            uris = getExpansionFromObject(data, getExpansionByLocator(data, folder["Uris"]["FolderHighlightImage"]), "ImageSizes")
        
        oc.add(
           DirectoryObject(
               key     = Callback(GetFolder, nickname=nickname, uri=folder["UrlPath"]),
               title   = folder["Name"],
               thumb   = uris["MediumImageUrl"] if uris != None and "MediumImageUrl" in uris else R("icon-default.png")
           )
       )

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
               url     = uris["LargestImageUrl"] if uris != None and "LargestImageUrl" in uris else R("icon-default.png")
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


