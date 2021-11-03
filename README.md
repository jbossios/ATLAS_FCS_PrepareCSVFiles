# Purpose

Create necessary input CSV files to use scripts from [RegressionWithKeras](https://github.com/jbossios/RegressionWithKeras) repository

## Create CSV files to train network to predict extrapolation weights

Script: *MakeCSVfiles_NN.py*

Use this script to produce CSV files from ROOT files to be used to train a DNN to predict extrapolation weights

### Dependencies

- ROOT
- pandas

### How to use?

This script will produce .txt files (containing average and RMS of each feature, needed for inference) and .csv files (needed for training)

- Set ```Particles```
  - One CSV file will be produced for each particle, eta range and energy
  - If more than one particle type is provided, pdgID will also be stored in the CSV files
- Set ```InputPATH```: path to input ROOT files
- Set ```OutputPATHBase```: location where output CSV files will be written (CSV files will be written inside a folder named accordingly the set of particles used)
- Set ```TTreeName```: name of the TTree available in the input ROOT files
- Set ```ProduceTXTs``` to ```True``` (unless TXTs were already produce and are available in the corresponding location)

Run it:

```
python MakeCSVfiles_NN.py
```

## Create CSV files with firstPCAbin values from FCS

Script: *MakeCSVfiles_FCS.py*

Use this script to produce CSV files from ROOT files with firstPCAbin values

### Dependencies

- ROOT

### How to use?

- Set ```InputPATH```: path to input ROOT files
- Set ```OutputPATH```: where output CSV files will be saved
- Set ```TTreeName```: name of TTree from input ROOT files

Run it:

```
python MakeCSVfiles_FCS.py
```
