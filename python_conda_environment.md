# Python environment to run the example scripts 

Let's build a python environment in order to run the example scripts out of the box.

General idea: install Anaconda and create a Python 2.7 environment with Scipy and RDkit. This is the easiest way
to run the code without running into trouble. Converting this repo to Python 3 may result in a lot of headaches. I do not recommend going through it unless you REALLY need to make it compatible with a Python 3 application. 

# Creation of Python environment step-by-step:

1. [Install Anaconda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html)

2. Create a python 2.7 environment called nfp-py2 (for neural fingerprints) and activate it:

```bash
$ conda create --name nfp-py2 python=2.7

$ conda activate nfp-py2 
```

3. Install a rdkit version that is compatible with Python 2.7 (note the tag '2018.09.1')
```bash
$ conda install -c rdkit rdkit=2018.09.1
```

4. Check if rdkit installation is successful by importing it from the Python console:

```bash
$ python

```

```python 
import rdkit
print rdkit.__version__
[Out]: '2018.09.1'
```

5. Install the other required packages:

```bash
$ conda install scipy autograd  
```

# Run examples

Using the environment created above, you can run the scripts in [experiments](experiments/).

For example, run the regression script:

```bash
$ python examples/regressions.py

```


