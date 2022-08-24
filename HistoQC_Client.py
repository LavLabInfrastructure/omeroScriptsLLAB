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
        'HistoQC', """This script runs HistoQC modules based on provided config file, served through omero api""",
        scripts.String("Data_Type", optional=False, grouping="1", description="Choose Datatype (Image, Dataset, Project)", values=dataTypes, default="Image"),
        scripts.List("IDs", optional=False, grouping="2",description="List of Image IDs to process.").ofType(rlong(0)),
        scripts.String("Config", optional=False, grouping="3",description="Config file to use. Config generator script coming soon", values=configs, default="Default"),
        version="0.10",
        authors=["Andrew Janowczyk", "Michael Barrett"],
        institutions=["CASE", "LaViolette Lab"],
        contact="mjbarrett@mcw.edu",
    )


    try:
        dataType = client.getInput("Data_Type", unwrap=True)
        rawIds = client.getInput("IDs", unwrap=True)
        ids=""
        for id in rawIds: ids=ids+(str(id))+"," # format list as csv string
        argv = f"{dataType}:{ids} -u root -w omero -s 0.0.0.0 -p 4064 --secure" # format vals into terminal command
        main(argv=argv)
        client.setOutput("Message", rstring("Success"))
    except Exception as e:
        print(e)
        client.setOutput("Message", rstring("Failed, See err message"))

    finally:
        client.closeSession()