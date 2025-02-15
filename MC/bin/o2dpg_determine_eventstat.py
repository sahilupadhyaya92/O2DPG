#!/usr/bin/env python3

#
# Script that determines final accounting numbers / event statistics
# for reporting back to MonaLisa.
#  
# Analyses the AO2D / kinematics output of an O2DPG simulation run 
# and creates a file of the form 
#
# inputN_passedN_errorsN_outputN.stat 
# 
# which is picked up and used by the MonaLisa system.
#
# See discussion in https://alice.its.cern.ch/jira/browse/O2-4553;
# Here outputN would be the number of events/collisions produced in this job.

import ROOT
import argparse
import os
import re

parser = argparse.ArgumentParser(description='',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-f','--aod-file', default="AO2D.root", help='AO2D file to check')
args = parser.parse_args()

def write_stat_file(eventcount):
    """
    writes a file conforming to MonaLisa convention
    """
    
    filename = '0_0_0_' + str(eventcount) + '.stat'
    # touche/create a new file
    with open(filename, 'w') as f:
      print ("#This file is autogenerated", file=f)
      print ("#It tells MonaLisa about the number of produced MC events", file=f)
      print ("#Numer of MC collisions in AOD : " + str(eventcount), file=f)

def read_collisioncontext_eventcount(file):
    """
    determines MC eventcount from collision context files
    """
    pass

def find_files_matching_pattern(directory='.', pattern='.*'):
    matching_files = []

    # Walk through the directory and its subdirectories
    for root, dirs, files in os.walk(directory):
      for file_name in files:
        # Check if the filename matches the regular expression pattern
        if re.match(pattern, file_name):
          matching_files.append(os.path.join(root, file_name))

    return matching_files

def read_GEANT_eventcount(file):
    # Open the ROOT file
    eventcount = 0
    tfile = ROOT.TFile.Open(file)
    if tfile:
      simtree = tfile.Get("o2sim")
      if simtree and isinstance(simtree, ROOT.TTree):
        eventcount = simtree.GetEntries()

      tfile.Close()
    return eventcount

def read_accumulated_GEANT_eventcount(directory = "."):
    """
    Determines the MC eventcount from GEANT kinematics files sitting
    in directory/tfX/ subdirectories.
    """
    pattern_to_match = r'sgn.*_Kine.root'
    kine_files = find_files_matching_pattern(directory, pattern_to_match)
    eventcount = 0
    for f in kine_files:
      eventcount = eventcount + read_GEANT_eventcount(f)
    return eventcount

def read_AO2D_eventcount(file):
    """
    determines MC eventcount from (final) AO2D file
    """
    eventcount = 0

    # Open the ROOT file
    tfile = ROOT.TFile.Open(file)

    # Get the list of keys (TKeys) in the ROOT files
    keys = tfile.GetListOfKeys()

    # Iterate through the keys "DF_" keys and accumulate
    # stored MC collisions
    colfound = 0

    for key in keys:
      key_name = key.GetName()
      if key_name.startswith("DF_"):
        obj = key.ReadObj()

        # get the list of keys of available tables
        tablelist = obj.GetListOfKeys()
        for tab in tablelist:
          # the O2mccollision_ tree contains the simulated collisions
          # but the version number might change so better to loop over keys and do matching
          tabname = tab.GetName()
          if re.match("^O2mccollision(_[0-9]*)?$", tabname):
            coltreekey = obj.GetKey(tabname)
            coltree = coltreekey.ReadObj()
            if coltree and isinstance(coltree, ROOT.TTree):
              eventcount = eventcount + coltree.GetEntries()
              colfound = colfound + 1

    if colfound == 0:
      print ("ERROR: No MC collision table found")

    # Close the files
    tfile.Close()
    return eventcount

AO2D_eventcount = read_AO2D_eventcount(args.aod_file)
GEANT_eventcount = read_accumulated_GEANT_eventcount()
if AO2D_eventcount != GEANT_eventcount:
    print ("WARN: AO2D MC event count and GEANT event count differ")

print ("Found " + str(AO2D_eventcount) + " events in AO2D file")
write_stat_file(AO2D_eventcount)
