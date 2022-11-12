# CislunarSim

Simulation Software for the Cislunar Explorers Mission  
[Read the Docs](https://cislunarsim.readthedocs.io/en/latest/)

## Getting Started

Create a virtual Python environment and install all the necessary dependencies. Make sure you run this from the root of the repository!

```bash
python -m venv venv
source venv/bin/activate
pip install -e .
```

You can exit this environment by running `deactivate`. To re-enter an existing environment, all you need is `source venv/bin/activate`.  

*Note: Some problems have been known to occur if your [pip](https://pypi.org/project/pip/) is not updated. Follow the warning prompt your terminal gives if this happens.*

## Running the Sim

#### Usage:

```zsh
python src/main.py {file path} [-v] [-l]
```

#### Options:  
`file path` *(Required)*: The path of the config file to simulate  
`-v` *(Optional)*: Verbose mode for logging extra information to the terminal  
`-l` *(Optional)*: Headless mode that will not generate a CSV nor plot any data

#### Examples:  
```zsh
python src/main.py configs/iss.json 
python src/main.py configs/test_angles.json -v
```

We recommend setting your `D_T` value (the timestep length) in `constants.py` to be between 100 - 300. If you're looking for a faster run, you'll want to set it to be on the higher side of that range.

## Plotting Sim Runs

#### Usage:  

```zsh
python src/utils/plot.py {file path}
```

#### Options:  
`file path` *(Required)*: The path of the csv file to plot  

#### Example:  
```zsh
python src/utils/plot.py runs/cislunarsim-355942804.csv
```

*Note: The above is an example CSV file that does not exist locally on your system.*

## IMPORTANT: Python Version MUST be >=3.8

Run `python --version` to find your Python version. If it's lower than 3.8, you must upgrade your Python version:

##### macOS:

If you don't already have [Homebrew](https://brew.sh/), run the following:

```zsh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then, upgrade your Python version

```zsh
brew update && brew upgrade python
```

and run the following command to set Python3 as the default interpreter

```zsh
cp /usr/local/bin/python3 /usr/local/bin/python
```

##### Windows: