
conda activate NiChartGUI
pip install .


ddir='/home/guraylab/AIBIL/Github/NiChartPackages/NiChartHarmonize/test_temp/Test3/outputs/EXP2_ALL_TrainTest'

NiChartGUI --data_file ${ddir}/Set_Test.csv --data_file ${ddir}/Set_Train.csv

NiChartGUI --data_file ${ddir}/Set_Test.csv
