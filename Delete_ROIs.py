#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) <year> Open Microscopy Environment.
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
Deletes all ROIs of requested omero images
Translated to OMERO.script from https://forum.image.sc/t/searching-and-removing-rois-in-omero-using-python-api/48910
"""

from omero.gateway import BlitzGateway
from omero.rtypes import rlong, rstring

import omero.scripts as scripts

# Deletes all rois in a list of Image Ids
def deleteROIs(conn, ids):
    print("Checking Images: " + str(ids))
    rois_removed = []
    for id in ids :
        try :
            result = conn.getObjects("roi", opts={'image' : id})
            roi_ids = []
            for roi in result :
                roi_ids.append(roi.getId())
                rois_removed.append(roi.getId())
            conn.deleteObjects("Roi", roi_ids)
        except AttributeError:
            print("no rois found for " + str(id))
    if rois_removed == [] :
        client.setOutput("Message", rstring("Failed: No ROIs found"))
        exit()
    else :
        print("ROIs Removed: " + rois_removed)



if __name__ == "__main__":

    dataTypes = [rstring('Image'),rstring('Dataset'),rstring('Project')]

    client = scripts.client(
        'deleteROIs', """This script deletes all ROIs of the given images""",

        scripts.String(
            "Data_Type", optional=False, grouping="1",
            description="Choose source of images",
            values=dataTypes, default="Image"),

        scripts.List(
            "Ids", optional=False, grouping="2",
            description="List of Ids to process.").ofType(rlong(0)),

        version="1",
        authors=["Michael Barrett", "Will Moore"],
        institutions=["LaViolette Lab", "The OME Consortium"],
        contact="mjbarrett@mcw.edu",
    )

    try:
        conn = BlitzGateway(client_obj=client)
        dataType = client.getInput("Data_Type", unwrap=True)
        rawIds = client.getInput("Ids", unwrap=True)
        # if it's not an image we have to search for the images
        if dataType != "Image" :
            # project to dataset
            if dataType == "Project" :
                projectIds = rawIds; rawIds = []
                for projectId in projectIds :
                    for dataset in conn.getObjects('dataset', opts={'project' : projectId}) :
                        rawIds.append(dataset.getId())
            # dataset to image
            ids=[]
            for datasetId in rawIds :
                for image in conn.getObjects('image', opts={'dataset' : datasetId}) :
                    ids.append(image.getId())
        # else rename image ids
        else :
            ids = rawIds
        deleteROIs(conn, ids)
        client.setOutput("Message", rstring("Success")) 

    except Exception as e:
        print(e)
        client.setOutput("Message", rstring("Failed:"))

    finally:
        client.closeSession()
