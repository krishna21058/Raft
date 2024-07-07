#!/bin/bash

python3 reset.py

node_ids=(1 2 3 4 5)

for node_id in "${node_ids[@]}"; do
    xterm -fa 'Monospace' -fs 10 -hold -e "echo $node_id | python3 node.py" &
done
