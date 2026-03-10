#!/bin/bash
MODEL="/home/jorge/piper/models/es_AR-daniela-high.onnx"
PIPER="/home/jorge/piper/piper/piper"
echo "$@" | $PIPER --model $MODEL --output_file - | aplay -q
