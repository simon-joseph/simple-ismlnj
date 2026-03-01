#!/usr/bin/env python3
"""Install the SML/NJ Jupyter kernel spec with correct paths for the current environment."""

import json
import os
import sys
import tempfile

from jupyter_client.kernelspec import KernelSpecManager


KERNEL_NAME = 'smlnj'


def main():
    src_dir = os.path.dirname(os.path.abspath(__file__))
    kernel_script = os.path.join(src_dir, 'smlnjkernel.py')

    kernel_json = {
        "display_name": "SML/NJ",
        "language": "smlnj",
        "argv": [sys.executable, kernel_script, "-f", "{connection_file}"],
        "codemirror_mode": "scheme"
    }

    with tempfile.TemporaryDirectory() as td:
        kernel_dir = os.path.join(td, KERNEL_NAME)
        os.makedirs(kernel_dir)
        with open(os.path.join(kernel_dir, 'kernel.json'), 'w') as f:
            json.dump(kernel_json, f, indent=2)

        ksm = KernelSpecManager()
        ksm.install_kernel_spec(kernel_dir, kernel_name=KERNEL_NAME, user=True, replace=True)

    print("SML/NJ kernel installed successfully.")
    print("  Python:  {}".format(sys.executable))
    print("  Script:  {}".format(kernel_script))


if __name__ == '__main__':
    main()
