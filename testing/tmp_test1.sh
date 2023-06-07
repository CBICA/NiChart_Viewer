
conda activate NiChartGUI
pip install .

ddir='/home/guray/Github/NiChartPackages/NiChartGUI/tmp_testing/EXP2_ALL_TrainTest'

# NiChartGUI --data_file ${ddir}/Set_Test.csv --data_file ${ddir}/Set_Train.csv
# NiChartGUI --data_file ${ddir}/Set_Test.csv

NiChartGUI --data_file ./in_data/Data_Test.csv --data_file ./in_data/Data_Train.csv 


