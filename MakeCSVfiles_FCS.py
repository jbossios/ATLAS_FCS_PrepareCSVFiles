##################################################################################################################
#                                                                                                                #
# Author:  Jona Bossio (jbossios@cern.ch)                                                                        #
# Purpose: Create CSV files from ROOT files with firstPCAbin values                                              #
#          This is needed to obtain the current extrapolation weights and compare with those predicted by the NN #
#                                                                                                                #
##################################################################################################################

# PATH to input ROOT files
InputPATH = '/eos/user/a/ahasib/Data/ParametrizationProductionVer15/'

# Where to locate output CSV files
OutputPATH = '/eos/user/j/jbossios/FastCaloSim/HasibInputsCSV/'

# Name of TTree
TTreeName = 'tree_1stPCA'

##################################################################################################################
# DO NOT MODIFY (everything below this line)
##################################################################################################################

import os,sys,csv
from ROOT import *

# CSV header
header = ['firstPCAbin']

# Loop over input files
for Folder in os.listdir(InputPATH):
  if 'pid' not in Folder: continue
  # Loop over files
  Folder = Folder+'/'
  for File in os.listdir(InputPATH+Folder):
    if 'FirstPCA_App' not in File: continue
    print('INFO: Preparing CSV file for {}'.format(InputPATH+Folder+File))

    # Get TTree
    tfile = TFile.Open(InputPATH+Folder+File)
    tree  = tfile.Get(TTreeName)

    # Open the CSV file
    outFileName = OutputPATH+File.replace('.root','.csv')
    outFile     = open(outFileName, 'w')
    
    # Create the csv writer
    writer = csv.writer(outFile)

    # write the header
    writer.writerow(header)
 
    # Loop over events
    for event in tree: 
      # write fraction of energy deposited on each layer
      row = [getattr(tree,var) for var in header]  # write PCA bin
      writer.writerow(row)
    
    # Close the files
    outFile.close()
    tfile.Close()

print('>>> ALL DONE <<<')
