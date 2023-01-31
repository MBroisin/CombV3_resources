#!/bin/bash

filestem=$1
duration_s=$2

duration_ms=$(( 1000 * duration_s ))
extension=".h264"

echo "Raspivid stuff"
raspivid -t ${duration_ms} -cfx 128:128 -fps 30 -o "$filestem$extension"

