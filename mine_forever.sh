#!/bin/bash
CLI="/Users/hamoudi/OpenSY/build/bin/opensy-cli"
ADDR="syl1q0y76xxxdfvhfad2sju4fymnsn8zs5lndpwhufw"

while true; do
    echo "$(date): Mining batch of 100 blocks..."
    $CLI generatetoaddress 100 $ADDR
    sleep 1
done
