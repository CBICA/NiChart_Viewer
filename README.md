# [NiChartGUI] The neuro-imaging brain aging chart

| :construction:
  <font size="+1">This software and documentation is under development!
                  Check out up-to-date documentation at
                  [cbica.github.io/NiChartGUI/](https://cbica.github.io/NiChartGUI/) </font> :construction: |
|-----------------------------------------|

The neuro-imaging brain aging chart **[NiChartGUI]** is a comprehensive solution to
analyze standard structural and functional brain MRI data across studies.
**[NiChartGUI]** and the associated pre-processing tools implement computational
morphometry, functional signal analysis, quality control, statistical
harmonization, data standardization, interactive visualization, and extraction
of expressive imaging signatures.

This `README` is intended for contributors and developers.
User documentation is available at
[cbica.github.io/NiChartGUI/](https://cbica.github.io/NiChartGUI/).


<figure>
  <img src="NiChartGUI/resources/workflow.gif" alt="[NiChartGUI] Demo"/>
  <figcaption>Demonstration of the [NiChartGUI] graphical user interface.</figcaption>
</figure>


## Setup for development
Install Python version 3.8.8 or newer.
The exact procedure depends on the operating system and configuration.
Verify the version with

```shell
python --version # should be 3.8.8 or newer
```


### Prepare conda environment
Assuming current working directory is `NiChartGUI` and containing the source code
cloned from https://github.com/CBICA/NiChartGUI.git.

Ensure Anaconda is installed. Follow instructions for user's operating system [here](https://docs.anaconda.com/anaconda/install/index.html). After Anaconda has been installed, be sure to exit and reopen any 
command line windows to use `conda` command


```shell
conda create -n NiChartGUI python=3.8.8  
conda activate NiChartGUI
python -m pip install --upgrade pip
```


### Prepare environment in Linux (CUBIC)
Assuming current working directory is `NiChartGUI` and containing the source code
cloned from https://github.com/CBICA/NiChartGUI.git.

```shell
python -m venv .env
.env/bin/activate
python -m pip install --upgrade pip
```

### Prepare environment for PowerShell (Windows 10 or 11)
Assuming current working directory is `NiChartGUI` and containing the source code
cloned from https://github.com/CBICA/NiChartGUI.git.

```shell
python -m venv .env
& .env/Scripts/Activate.ps1
python -m pip install --upgrade pip
```


### Install the [NiChartGUI] software
To install the [NiChartGUI], install it in a virtual or conda environment.
Depending on the desired version, use one of the following
commands to install it.

```shell
# Editable version for development after cloning https://github.com/CBICA/NiChartGUI.git 
python -m pip install -U -e .
poetry install

# Version from pull request (#57 in this example) for testing proposed changes
python -m pip install -U git+https://github.com/CBICA/NiChartGUI.git@refs/pull/57/head

# Main version of toolbox
python -m pip install -U git+https://github.com/CBICA/NiChartGUI.git
```


## Usage
After proper installation, the standalone graphical user interface can be launched
in the terminal with:

```shell
NiChartGUI
```

The data file can be passed as command line argument `--data_file` as shown below.

```shell
NiChartGUI --data_file istaging.pkl.gz
```

## Build executable package for Windows 10/11
We use (beeware/briefcase)[https://github.com/beeware/briefcase)] to package
the software in Windows 10/11.

```shell
briefcase create 
briefcase update
briefcase package
```

The result is an installer `NiChartGUI.msi` that will install the app in the
user's profile. The installation does not require administrator rights.

## Disclaimer
- The software has been designed for research purposes only and has neither been reviewed nor approved for clinical use by the Food and Drug Administration (FDA) or by any other federal/state agency.
- By using NiChartGUI, the user agrees to the following license: https://www.med.upenn.edu/cbica/software-agreement-non-commercial.html

## Contact
For more information and support, please post on the [Discussions](https://github.com/CBICA/NiChartGUI/discussions) section or contact <a href="mailto:software@cbica.upenn.edu">CBICA Software</a>.
