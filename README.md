# [NiChartGUI] The neuro-imaging brain aging chart

| :construction:
  <font size="+1">This software and documentation is under development!
  </font> 
  :construction: |
|-----------------------------------------|

NiChart viewer **[NiChart_Viewer]** is a toolbox for NiChart MRI features and biomarkers.

## Installation

```shell
conda create -n NiChart_Viewer python=3.8.8  
conda activate NiChart_Viewer
conda install pip
pip install .
```

## Note

Harmonization plugin requires installation of the NiChartHarmonize package (https://github.com/gurayerus/NiChartHarmonize)

SPARE plugin requires installation of the NiChartSPARE package (https://github.com/georgeaidinis/spare_score)


## Usage

```shell
NiChart_Viewer --data_file infile1.csv --data_file infile2.csv ...
```

## Disclaimer
- The software has been designed for research purposes only and has neither been reviewed nor approved for clinical use by the Food and Drug Administration (FDA) or by any other federal/state agency.
- By using NiChart_Viewer, the user agrees to the following license: https://www.med.upenn.edu/cbica/software-agreement-non-commercial.html

## Contact
<a href="mailto:guray.erus@pennmedicine.upenn.edu">Guray Erus</a>.
