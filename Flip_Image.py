
"""
This script runs HistoQC modules based on provided config file, served through omero api
"""

import numpy as np
from omero.rtypes import rlong, rstring
from omero.gateway import BlitzGateway
import omero.scripts as scripts
# mirrors a given list of tiles
def flipImg(pixSource, pid, tileList, axis):
    sizeX, sizeY = pixSource.getSizeX(), pixSource.getSizeX()
    rps=pixSource._conn.createRawPixelsStore()
    i=0
    for tile in pixSource.getTiles(tileList):
        rps.setPixelsId(pid,False)
        tile=np.flip(tile, axis)

        z,c,t,xywh=tileList[i]
        x,y,w,h=xywh
        print(rps.getPixelsId())
        print(tile)
        # gotta flip tile pos too
        if axis == 1: # ^-v
            rps.setTile(tile.tobytes(), z, c, t, x, (sizeY-y),w,h)
        else: # <->
            rps.setTile(tile.tobytes(), z, c, t, (sizeX-x),y,w,h)

        i+=1 


# flips everything under a given image
def flipSeries(img, axis): #((z,c,t),(x,y))

    pix=img.getPrimaryPixels()
    sizeX,sizeY,sizeZ,sizeC,sizeT=pix.getSizeX(),pix.getSizeY(),pix.getSizeZ(),pix.getSizeC(),pix.getSizeT()
    channels=range(sizeC)
    name='MIRRORED_'+img.getName()
    desc = img.getDescription() + ' Mirrored using Flip_Image.py'

    pixType=None
    query=conn.getQueryService()
    pixType=query.findByQuery(f"from PixelsType as p where p.value='{pix.getPixelsType().value}'", None)

    newImgId=None
    service=conn.getPixelsService()
    newImgId=service.createImage(sizeX,sizeY,sizeZ,sizeT,channels,pixType, name, desc)
    rps= img._conn.createRawPixelsStore() 
    rps.setPixelsId(pix.getId(), False)
    dim=rps.getResolutionDescriptions()[rps.getResolutionLevels()-1]
    tileSize=rps.getTileSize()
    tileList=getTileList((sizeZ,sizeC,sizeT),dim,tileSize)
    flipImg(pix,newImgId._val,tileList,axis)

    return newImgId._val

def getTileList(zctSize, dim, tileSize):
    tileList=[]
    for z in range(zctSize[0]): # each layer
        for c in range(zctSize[1]): # each channel
            for t in range(zctSize[2]): # each time point 
                for y in range(0,dim.sizeY,tileSize[1]):
                    for x in range(0,dim.sizeX,tileSize[0]):
                        tileList.append((z,c,t,(x,y,tileSize[0],tileSize[1])))
    return tileList


if __name__ == "__main__":
    flipDirections = [rstring('Horizontal'),rstring('Vertical')]
    client = scripts.client(
        'Flip Image', """Flips a given set of images vertically or horizontally""",
        scripts.List("Image_Ids", optional=True, grouping="1",description="List of Image IDs to process.", default=None).ofType(rlong(0)),
        scripts.List("Dataset_Ids", optional=True, grouping="2",description="List of Dataset IDs to process.", default=None).ofType(rlong(0)),
        scripts.List("Project_Ids", optional=True, grouping="3",description="List of Project IDs to process.", default=None).ofType(rlong(0)),
        scripts.String("Flip_Orientation", optional=False, grouping="4",description="Direction to flip images.", values=flipDirections, default=rstring("Horizontal")),
        version="0.10",
        authors=["Andrew Janowczyk", "Michael Barrett"],
        institutions=["CASE", "LaViolette Lab"],
        contact="mjbarrett@mcw.edu",
    )

    imgIds = client.getInput("Image_Ids", unwrap=True)
    dsIds = client.getInput("Dataset_Ids", unwrap=True)
    projIds = client.getInput("Project_Ids", unwrap=True)
    orientation = client.getInput("Flip_Orientation", unwrap=True)
    if imgIds == None and dsIds == None and projIds == None:
        client.setOutput("Message", rstring("Failed, No images provided"))
        exit(1)

    try:
        conn = BlitzGateway(client_obj=client)
        # if it's not an image we have to search for the images
        ids=[]
        if projIds != None:
            for p in projIds:
                for id in conn.getObjects('Image', opts={'project':p}):
                    ids.append(id)
        if dsIds != None:
            for ds in dsIds:
                for id in conn.getObjects('Image',opts={'dataset':ds}):
                    ids.append(id)
        if imgIds != None:
            for id in imgIds:
                ids.append(id)

        # set flip direction
        axis = True if orientation == "Horizontal" else False

        # check and report perms
        group = conn.getGroupFromContext()
        group_perms = group.getDetails().getPermissions()
        perm_string = str(group_perms)
        permission_names = {
            'rw----': 'PRIVATE',
            'rwr---': 'READ-ONLY',
            'rwra--': 'READ-ANNOTATE',
            'rwrw--': 'READ-WRITE'}
        print("Permissions: %s (%s)" % (permission_names[perm_string], perm_string))
        if permission_names[perm_string] != 'READ-WRITE':
            client.setOutput("Message", rstring("Failed, Required write permission."))
            exit(1)

        # flip each requested image
        for id in ids:
            img=conn.getObject('Image', id)
            newId=flipSeries(img, axis)
            print('Mirrored Image: %s, %sly' % (img.getName(), orientation))
        client.setOutput("Message", rstring("Success")) 

    except Exception as e:
        print(e)
        client.setOutput("Message", rstring("Failed"))

    finally:
        client.closeSession()

