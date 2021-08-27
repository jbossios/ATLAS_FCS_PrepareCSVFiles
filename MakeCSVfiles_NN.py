######################################################
#                                                    #
# Author:  Jona Bossio (jbossios@cern.ch)            #
# Purpose: Create CSV files from ROOT files          #
#          This CSV files will be used to train a NN #
#                                                    #
######################################################

#!/usr/bin/env python3

Particle = 'photons'

# PATH to input ROOT files
InputPATH = '/eos/user/j/jbossios/FastCaloSim/MicheleInputs/'

# Where to locate output CSV files
OutputPATH = '/eos/user/j/jbossios/FastCaloSim/MicheleInputsCSV/'

# Name of TTree
TTreeName = 'rootTree'

#############################################
# DO NOT MODIFY (everything below this line)
#############################################

InputPATH  += '{}/'.format(Particle)
OutputPATH += '{}/'.format(Particle)

import os,sys,csv
from ROOT import *
from ROOT import RDataFrame
import pandas as pd

# CSV header
Layers  = [0,1,2,3,12]
if Particle == 'pions': Layers += [13,14]
header  = ['e_{}'.format(x) for x in Layers]
header += ['ef_{}'.format(x) for x in Layers]
header += ['extrapWeight_{}'.format(x) for x in Layers]
header += ['etrue']

# Create a single DF per eta bin to then extract Mean and Std. Dev. 
DFs = dict()
for File in os.listdir(InputPATH):

  # skip (non-) phiCorrected files for (pions) electrons
  if Particle == 'pions'     and 'phiCorrected' in File: continue
  if Particle == 'electrons' and 'phiCorrected' not in File: continue
  
  # Read true energy from input filename
  Energy = File.split('_')[1].split('E')[1]

  # Read eta range from input filename
  EtaBin = 'eta_{}_{}'.format(File.split('eta_')[1].split('_')[0],File.split('eta_')[1].split('_')[1])

  # Create DF
  DF          = RDataFrame(TTreeName,InputPATH+File)                        # create RDataFrame from TTree
  npy         = DF.AsNumpy()                                                # convert RDataFrame to numpy
  df          = pd.DataFrame(data=npy, columns=[key for key in npy.keys()]) # convert to pandas/DataFrame
  df['etrue'] = float(Energy)                                               # add new column with true energy
  if EtaBin not in DFs:
    DFs[EtaBin] = df
  else:
    DFs[EtaBin] = pd.concat([DFs[EtaBin],df],ignore_index=True)

# Take Mean and Std. Dev. values for all features (energy fractions and true energy)
Means   = dict()
StdDevs = dict()
for EtaBin,DF in DFs.items():
  counter = 0
  for layer in Layers:
    if counter == 0:
      DF['totalEnergy'] = DF['e_{}'.format(layer)]
    else:
      DF['totalEnergy'] += DF['e_{}'.format(layer)]
    counter += 1
  DF = DF[DF['totalEnergy'] > 0]
  for layer in Layers:
    DF['ef_{}'.format(layer)] = DF.apply(lambda row: row['e_{}'.format(layer)] / row['totalEnergy'], axis = 1)
  Means[EtaBin]   = { var : DF[var].mean() for var in header if 'ef_' in var or var == 'etrue' }
  StdDevs[EtaBin] = { var : DF[var].std()  for var in header if 'ef_' in var or var == 'etrue' }
  # save them
  outTxtFileName = OutputPATH+'MeanStdDevEnergyFractions_{}'.format(EtaBin)+'.txt'
  outTxtFile     = open(outTxtFileName,'w')
  for key in Means[EtaBin]:
    outTxtFile.write('{} {} {}\n'.format(key,Means[EtaBin][key],StdDevs[EtaBin][key]))
  outTxtFile.close()

# Loop over input files
for File in os.listdir(InputPATH):

  # skip (non-) phiCorrected files for (pions) electrons
  if Particle == 'pions'     and 'phiCorrected' in File:     continue
  if Particle == 'electrons' and 'phiCorrected' not in File: continue

  print('INFO: Preparing CSV file for {}'.format(InputPATH+File))

  # Read true energy from input filename
  Energy = File.split('_')[1].split('E')[1]

  # Read eta range from input filename
  EtaBin = 'eta_{}_{}'.format(File.split('eta_')[1].split('_')[0],File.split('eta_')[1].split('_')[1])

  # Get TTree
  tfile = TFile.Open(InputPATH+File)
  if not tfile:
    print('ERROR: {} not found, exiting'.format(InputPATH+File))
    sys.exit(1)
  tree  = tfile.Get(TTreeName)
  if not tree:
    print('WARNING: {} not found in {}, file will be skipped'.format(TTreeName,InputPATH+File))
    continue # skip file

  # Open the CSV file
  outFileName = OutputPATH+File.replace('.root','.csv')
  outFile     = open(outFileName, 'w')
  
  # Create the csv writer
  writer = csv.writer(outFile)

  # write the header
  writer.writerow(header)

  maxEvents = -1

  # Temporary fix due to problem with input TTree for E2097152
  if 'E2097152' in File:
    maxEvents = 2000
 
  # Loop over events
  counter = 0
  for event in tree: 
    counter += 1
    if maxEvents != -1:
      if counter > maxEvents: break
    # write a row to the csv file
    totalEnergy = 0 # total deposited energy
    for var in header:
      if 'e_' in var:
        totalEnergy += getattr(tree,var)
    # write fraction of energy deposited on each layer
    row = []
    for var in header:
      if 'e_' in var:
        row.append(getattr(tree,var))
      elif 'ef_' in var:
        energyFraction = ((getattr(tree,var.replace('ef','e'))/totalEnergy)-Means[EtaBin][var])/StdDevs[EtaBin][var] if totalEnergy!=0 and StdDevs[EtaBin][var]!=0 else 0
        row.append(energyFraction)
    row += [getattr(tree,var) for var in header if 'extrapWeight_' in var]         # write extrapolation weight on each layer
    row.append( (float(Energy)-Means[EtaBin]['etrue']) / StdDevs[EtaBin]['etrue']) # write truth particle's energy
    writer.writerow(row)
  
  # Close the files
  outFile.close()
  tfile.Close()

print('>>> ALL DONE <<<')
