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
This script runs HistoQC modules based on provided config file, served through omero api
"""

from histoqc.__main__ import main
from omero.rtypes import rlong, rstring
import omero.scripts as scripts

if __name__ == "__main__":
    # --- server-side client interface -----------------------------------
    dataTypes = [rstring('Image'), rstring('Dataset'), rstring('Project')]
    configs=[rstring("Default")] #TODO
    client = scripts.client(
        'HistoQC', """Runs HistoQCxOMERO with the given params""",
        scripts.List("Image_Ids", optional=True, grouping="1",description="List of Image IDs to process.", default=None).ofType(rlong(0)),
        scripts.List("Dataset_Ids", optional=True, grouping="2",description="List of Dataset IDs to process.", default=None).ofType(rlong(0)),
        scripts.List("Project_Ids", optional=True, grouping="3",description="List of Project IDs to process.", default=None).ofType(rlong(0)),
        scripts.String("Config", optional=True, grouping="4",description="Config file to use. Config generator script coming soon", values=configs, default=None),
        scripts.Int("Number_Of_Processes", optional=True, grouping="5",description="number of processes to launch", default=None),
        scripts.Int("Batch", optional=True, grouping="6",description="break results file into subsets of this size", default=None),
        scripts.String("Base_Path", optional=True, grouping="7",description="helps when producing data using existing output file as input", default=None),
        version="0.10",
        authors=["Andrew Janowczyk", "Michael Barrett"],
        institutions=["CASE", "LaViolette Lab"],
        contact="mjbarrett@mcw.edu",
    )

    argv=""
    imgIds = client.getInput("Image_Ids", unwrap=True)
    dsIds = client.getInput("Dataset_Ids", unwrap=True)
    projIds = client.getInput("Project_Ids", unwrap=True)
    cfg = client.getInput("Config", unwrap=True)
    nproc = client.getInput("Number_Of_Processes", unwrap=True)
    nbatch = client.getInput("Batch", unwrap=True)
    bpath = client.getInput("Base_Path", unwrap=True)

    if imgIds == None and dsIds == None and projIds == None:
        client.setOutput("Message", rstring("Failed, No images provided"))
        exit(1)

    if cfg != None:
        argv+=f"-c {cfg} "

    if nproc != None:
        argv+=f"-n {nproc} "

    if nbatch != None:
        argv+=f"-b {nbatch} "

    if bpath != None:
        argv+=f"-P {bpath} "

    if projIds != None:
        argv+="Project:"
        for id in projIds: argv+= f"{str(id)}," 

    if dsIds != None:
        argv+="Dataset:"
        for id in dsIds: argv+= f"{str(id)}," 

    if imgIds != None:
        for id in imgIds: argv+= f"{str(id)}," 

    try:
        main(client=client, argv=argv)
        client.setOutput("Message", rstring("Success"))

    except Exception as e:
        print(e)
        client.setOutput("Message", rstring("Failed, See err message"))

    finally:
        client.closeSession()