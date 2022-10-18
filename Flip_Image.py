
"""
This script runs HistoQC modules based on provided config file, served through omero api
"""

import numpy as np
from omero.rtypes import rlong, rstring
from omero.gateway import BlitzGateway, ImageWrapper
import omero.scripts as scripts

def flipPlane(pix, z , c, t, horizontalBool):
    width, height=pix.getSizeX(), pix.getSizeY()
    tileSize=pix.getTileSize()
    plane=np.empty((height,width), dtype=np.uint8)
    for y in range(0,height,tileSize[1]):
        for x in range(0,width,tileSize[0]):
            plane[y:y+tileSize[1]][x:x+tileSize[0]]=pix.getTile(z,c,t(x,y,width,height))


    return np.flip(plane, axis=horizontalBool)
def flipImage(pix, zct, horizontalBool):
    for z in range(zct[0]): # each layer
        for c in range(zct[1]): # each channel
            for t in range(zct[2]): # each time point 
                yield flipPlane(pix,z,c,t,horizontalBool)

def generateList(zct,tileSize): #((z,c,t),(x,y))
    for z in range(zct[0]): # each layer
        for c in range(zct[1]): # each channel
            for t in range(zct[2]): # each time point 
                for y in range(tileSize[1]): # height
                    for x in range(tileSize[0]): # width
                        appendtolist
                yield list # list of all tiles at a zct point
       


if __name__ == "__main__":
    flipDirections = [rstring('Horizontal'),rstring('Vertical')]
    client = scripts.client(
        'HistoQC', """Runs HistoQCxOMERO with the given params""",
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
        flipDir = True if orientation == "Horizontal" else False

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
            #exit(1)

        # generate and upload flipped images
        for id in ids:
            img=conn.getObject('Image', id)
            pixels=img.getPrimaryPixels()
            desc = "Image created from a hard-coded arrays"
            zct=(img.getSizeZ(), img.getSizeC(), img.getSizeT())
            ds=img.getParent() if img.getParent() != None else "Mirrored"
            i=conn.createImageFromNumpySeq(
                flipImage(img.getPrimaryPixels(), zct, flipDir),"test", sizeZ=zct[0],sizeC=zct[1],sizeT=zct[2], description=desc, dataset=img.getParent()) 
            print('Created new Image:%s Name:"%s"' % (i.getId(), i.getName()))
        client.setOutput("Message", rstring("Success")) 

    except Exception as e:
        print(e)
        client.setOutput("Message", rstring("Failed"))

    finally:
        client.closeSession()

