# simple-ismlnj
SML/NJ simple kernel for Jupyter/IPython Notebook

## Requirements

- [SML/NJ](https://smlnj.org/) installed and `sml` on your `PATH`
- Python 3 with `jupyter`, `ipykernel`, and `pexpect`:
  ```
  pip install jupyter ipykernel pexpect
  ```

## Installation

Clone the repository and run the install script:

```
git clone https://github.com/simon-joseph/simple-ismlnj.git
cd simple-ismlnj
python3 install_kernel.py
```

This registers the SML/NJ kernel using your current Python interpreter and
the correct path to `smlnjkernel.py`, so it works regardless of where you
cloned the repository.

## Docker

A `Dockerfile` is provided that installs SML/NJ 110.99.9 and the kernel in
one step:

```
docker build -t simple-ismlnj .
docker run -p 8888:8888 simple-ismlnj
```
