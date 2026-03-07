# PAFSSP Instances

Instances for the Permutation Assembly Flow-Shop Scheduling Problem (PAFSSP),
formatted as JSON files with two fields:

- `"p"`: processing times
- `"edges"`: precedence constraints in the machine graph

> **Note:** machines are indexed starting at 0.

## Processing times

`p` is a job-wise list of lists, where `p[j][m]` is the processing time of job `j` on machine `m`.

## Precedence edges

`edges` is a list of pairs `[j, k]`, each representing a directed edge from machine `j` to machine `k` in the machine precedence graph.
