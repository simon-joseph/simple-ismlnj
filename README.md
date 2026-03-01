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

## Timeout

By default, cell execution has **no timeout** — the kernel will wait
indefinitely for SML/NJ to produce a result.

To set a per-cell timeout (in seconds), add a `%timeout` magic directive at
the top of the cell:

```sml
%timeout 30
fun fib 0 = 0
  | fib 1 = 1
  | fib n = fib (n-1) + fib (n-2);

fib 35;
```

If execution exceeds the specified duration, the kernel will stop it, print a
timeout message, and restart the SML/NJ session. The `%timeout` line is
stripped before the code is sent to SML/NJ, so it won't cause syntax errors.

Cells without `%timeout` continue to run with no time limit.
