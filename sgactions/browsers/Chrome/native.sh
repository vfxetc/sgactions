#!/bin/bash

source ~/.bashrc

exec python "$(dirname "$0")"/native.py
