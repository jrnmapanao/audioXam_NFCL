FROM nvidia/cuda:10.1-base-ubuntu18.04
# FROM nvidia/cuda:11.2.0-cudnn8-runtime-ubuntu18.04
# FROM nvidia/cuda:11.3.1-cudnn8-runtime-ubuntu18.04
LABEL maintainer="https://github.com/mimbres/neural-audio-fp" 

RUN apt-get update
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PATH /opt/conda/bin:$PATH

RUN apt-get update --fix-missing && apt-get install -y wget bzip2 ca-certificates \
    libglib2.0-0 libxext6 libsm6 libxrender1 \
    git mercurial subversion

# Miniconda3
RUN wget --quiet \
    https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh \
    && /bin/bash ~/miniconda.sh -b -p /opt/conda \
    && rm ~/miniconda.sh && \ 
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc

RUN apt-get install -y libopenblas-dev

RUN apt-get install -y curl grep sed dpkg git tmux nano htop && \
    apt-get clean

RUN apt-get install -y python3-pip
RUN pip3 install --upgrade pip

COPY environment.yml /tmp/
RUN conda env create -f /tmp/environment.yml
       
RUN mkdir /work && mkdir /work/neural-audio-fp-dataset
WORKDIR /work
RUN git clone https://github.com/mimbres/neural-audio-fp.git ./neural-audio-fp

RUN echo "cd /work/" >> ~/.bashrc
RUN echo "conda activate fp" >> ~/.bashrc
RUN echo "conda env list" >> ~/.bashrc
CMD [ "/bin/bash" ]
