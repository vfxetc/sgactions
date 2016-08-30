#!/bin/bash

export PATH=$PATH:~/node_modules/jpm/bin
exec jpm watchpost --post-url http://127.0.0.1:8888/

