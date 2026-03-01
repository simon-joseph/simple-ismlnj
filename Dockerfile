FROM python:latest

ENV HOME /root
WORKDIR $HOME

RUN pip install --no-cache-dir jupyter ipykernel pexpect

ENV SMLROOT /usr/local/sml
WORKDIR $SMLROOT

# SML/NJ

## Install `gcc` for the C runtime that SML/NJ requires.
RUN apt-get update && apt-get install -y gcc

RUN wget -O - https://smlnj.org/dist/working/110.99.9/config.tgz | tar zxvf -
RUN config/install.sh -default 64

ENV PATH $SMLROOT/bin:$PATH

## Add Kernel

COPY . $HOME/sml
WORKDIR $HOME/sml

RUN jupyter kernelspec install kernels/smlnj

WORKDIR $HOME/notebook
CMD ["jupyter", "notebook", "--no-browser", "--allow-root", "--ip='*'"]
