######################################################
#                                                    #
# Purpose: Create CSV files from ROOT files          #
#          This CSV files will be used to train a NN #
# Author:  Jona Bossio (jbossios@cern.ch)            #
# Usage:   MakeCSVfiles_NN.py                        #
#                                                    #
######################################################

#!/usr/bin/env python3

#Particles = ['pions']
#Particles = ['photons']
#Particles = ['electrons']
#Particles = ['pions','electrons','photons']
#Particles = ['pions','electrons']
Particles = ['electrons','photons']

# PATH to input ROOT files
InputPATH = '/eos/user/j/jbossios/FastCaloSim/MicheleInputs/'

# Where to locate output CSV files
OutputPATHBase = '/eos/atlas/atlascerngroupdisk/proj-simul/AF3_Run3/Jona/MicheleInputsCSV/'

# Name of TTree
TTreeName = 'rootTree'

# Produce .txt files
ProduceTXTs = True # if False, will read already produced TXT files

#############################################
# DO NOT MODIFY (everything below this line)
#############################################

InputPATHs = { Particle : '{}{}/'.format(InputPATH,Particle) for Particle in Particles }
if len(Particles) == 1:
  OutputPATH = OutputPATHBase+'{}/'.format(Particles[0])
else:
  OutputPATH = OutputPATHBase+'_and_'.join(Particles)+'/'

import os,sys,csv
from ROOT import *
from ROOT import RDataFrame
import pandas as pd
from copy import deepcopy as dp

# Output CSV header
Layers  = [0,1,2,3,12]
if 'pions' in Particles: Layers += [13,14]
header  = ['e_{}'.format(x) for x in Layers]
header += ['ef_{}'.format(x) for x in Layers]
header += ['extrapWeight_{}'.format(x) for x in Layers]
header += ['etrue']
if len(Particles) > 1:
  header += ['pdgId']

# Mean and Std. Dev. values for all features (energy fractions and true energy)
Means   = dict()
StdDevs = dict()

# Create a single DF per eta bin to then extract Mean and Std. Dev.
DFs = dict()

if ProduceTXTs:
  # Create a single DF per eta bin to then extract Mean and Std. Dev.
  dFs = dict()

  # Loop over particles
  for Particle in Particles:

    for File in os.listdir(InputPATHs[Particle]):

      # skip (non-) phiCorrected files for (pions) electrons
      if Particle == 'pions'     and 'phiCorrected' in File: continue
      if Particle == 'electrons' and 'phiCorrected' not in File: continue

      # Read true energy from input filename
      Energy = File.split('_')[1].split('E')[1]

      # Read eta range from input filename
      EtaBin = 'eta_{}_{}'.format(File.split('eta_')[1].split('_')[0],File.split('eta_')[1].split('_')[1])
      EtaBin = EtaBin.replace('.root','')

      # Create DF
      DF          = RDataFrame(TTreeName,InputPATHs[Particle]+File)             # create RDataFrame from TTree
      npy         = DF.AsNumpy()                                                # convert RDataFrame to numpy
      df          = pd.DataFrame(data=npy, columns=[key for key in npy.keys()]) # convert to pandas/DataFrame
      # remove things I don't need
      Variables   = ['e_{}'.format(x) for x in Layers]
      Variables  += ['extrapWeight_{}'.format(x) for x in Layers]
      if (Particle == 'photons' or Particle == 'electrons') and 'pions' in Particles:
        for layer in ['13','14']:
          Variables.remove('e_{}'.format(layer))
          Variables.remove('extrapWeight_{}'.format(layer))
      df = df[Variables]
      # add new column with true energy
      df['etrue'] = float(Energy)
      # add dummy data
      if Particle == 'electrons' or Particle == 'photons':
        df.insert(5, 'e_13',            0.0)
        df.insert(6, 'e_14',            0.0)
        df.insert(12, 'extrapWeight_13', 0.0)
        df.insert(13, 'extrapWeight_14', 0.0)
      if EtaBin not in DFs:
        DFs[EtaBin] = df
      else:
        DFs[EtaBin] = pd.concat([DFs[EtaBin],df],ignore_index=True)

  # Take Mean and Std. Dev. values for all features (energy fractions and true energy)
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
else: # read TXTs
  for File in os.listdir(OutputPATH):
    if '.txt' not in File: continue
    if '.swp' in File: continue
    EtaBin = 'eta'+File.split('_eta')[1].replace('.txt','')
    Means[EtaBin]   = dict()
    StdDevs[EtaBin] = dict()
    txtFile = open(OutputPATH+File)
    if not txtFile:
      print('ERROR: {} not found ,exiting'.format(OutputPATH+File))
      sys.exit(1)
    for line in txtFile:
      Values               = line.split(' ')
      key                  = Values[0].replace('\n','')
      Means[EtaBin][key]   = float(Values[1].replace('\n',''))
      StdDevs[EtaBin][key] = float(Values[2].replace('\n',''))

# Loop over particles
for Particle in Particles:
  # Loop over input files
  for File in os.listdir(InputPATHs[Particle]):

    # skip (non-) phiCorrected files for (pions) electrons
    if Particle == 'pions'     and 'phiCorrected' in File:     continue
    if Particle == 'electrons' and 'phiCorrected' not in File: continue

    print('INFO: Preparing CSV file for {}'.format(InputPATHs[Particle]+File))

    # Read true energy from input filename
    Energy = File.split('_')[1].split('E')[1]

    # Read eta range from input filename
    EtaBin = 'eta_{}_{}'.format(File.split('eta_')[1].split('_')[0],File.split('eta_')[1].split('_')[1])
    EtaBin = EtaBin.replace('.root','')

    # Get TTree
    tfile = TFile.Open(InputPATHs[Particle]+File)
    if not tfile:
      print('ERROR: {} not found, exiting'.format(InputPATHs[Particle]+File))
      sys.exit(1)
    tree  = tfile.Get(TTreeName)
    if not tree:
      print('WARNING: {} not found in {}, file will be skipped'.format(TTreeName,InputPATHs[Particle]+File))
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
          totalEnergy += getattr(tree,var,0.0)
      # write fraction of energy deposited on each layer
      row = []
      for var in header:
        if 'e_' in var:
          row.append(getattr(tree,var,0.0))
        elif 'ef_' in var:
          energyFraction = ((getattr(tree,var.replace('ef','e'),0.0)/totalEnergy)-Means[EtaBin][var])/StdDevs[EtaBin][var] if totalEnergy!=0 and StdDevs[EtaBin][var]!=0 else 0
          row.append(energyFraction)
      row += [getattr(tree,var,0.0) for var in header if 'extrapWeight_' in var]     # write extrapolation weight on each layer
      row.append( (float(Energy)-Means[EtaBin]['etrue']) / StdDevs[EtaBin]['etrue']) # write truth particle's energy
      # write pdgid using one hot encoding
      if len(Particles) > 1:
        pdgid = {'electrons':0,'photons':1,'pions':2}[Particle]
        row.append(pdgid) # write pdgid
      writer.writerow(row)

    # Close the files
    outFile.close()
    tfile.Close()

print('>>> ALL DONE <<<')
