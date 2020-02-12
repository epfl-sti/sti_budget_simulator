#!/usr/bin/env bash

docker build -t epfl_sti/budget_simulator_jupyter_notebook:latest ./scripts

docker run --rm \
            -p 8888:8888 \
            -e JUPYTER_ENABLE_LAB=yes \
            -v "$PWD":/home/jovyan/work \
            --name budget_simulator_jupyter_notebook \
            epfl_sti/budget_simulator_jupyter_notebook
