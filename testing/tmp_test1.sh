
conda activate NiChart_Viewer
pip install .

ddir='/home/guray/Github/NiChartPackages/NiChart_Viewer/tmp_testing/EXP2_ALL_TrainTest'

# NiChart_Viewer --data_file ${ddir}/Set_Test.csv --data_file ${ddir}/Set_Train.csv
# NiChart_Viewer --data_file ${ddir}/Set_Test.csv

NiChart_Viewer --data_file ./in_data/Data_Test.csv --data_file ./in_data/Data_Train.csv 


