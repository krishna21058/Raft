# Raft

## About The Project
This project implements a modified Raft system with a leader lease modification, similar to those used by geo-distributed database clusters like [CockroachDB](https://www.cockroachlabs.com/) and [YugabyteDB](https://www.yugabyte.com/). Raft is a consensus algorithm designed for distributed systems to ensure fault tolerance and consistency. It operates through leader election, log replication, and the commitment of entries across a cluster of nodes. The goal is to build a database that stores key-value pairs, mapping strings (key) to strings (value).

### Built With
* [Python](https://www.python.org/)
* [gRPC](https://grpc.io/)
* [Google Cloud](https://cloud.google.com/)

### Table of Contents
<details open="open">
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#about-the-project">About The Project</a></li>
    <li><a href="#documentation">Documentation</a></li>
    <li><a href="#getting-started">Getting Started</a></li>
    <li><a href="#deployment">Deployment</a></li>
  </ol>
</details>

# Documentation
### Storage and Database Options

Raft nodes store and retrieve key-value pairs and replicate this data among other nodes fault-tolerantly. The nodes persist data (logs) locally in a human-readable format (.txt) along with metadata (commitLength, Term, and NodeID). This data is retrieved when the node restarts.

* #### Top level directory layout:
        .Raft/
        ├── client.py                 # Contains code for client operations
        ├── node.py                   # Contains code for node initialization and operations
        ├── logs_node_1               # Node initalized with id 1
        |   ├── dump
        |   ├── logs
        |   ├── metadata
        ├── logs_node_2               # Node initalized with id 2
        |   ├── dump
        |   ├── logs
        |   ├── metadata

* #### Operations supported:

        SET K V: Maps the key K to value V; for example, {SET x hello}. (WRITE OPERATION)
        GET K: Returns the latest committed value of key K.

        * If K doesn’t exist in the database, an empty string will be returned as value by default. (READ OPERATION)

* #### logs
        NO-OP 0
        SET name1 Alice 0 [SET {key} {value} {term}]
        SET name2 Bob 0
        SET name3 Bob 1

* #### dump
        Vote granted for Node 4 in term 8.
        Leader 3 lease renewal failed. Stepping Down.
        Node 3 accepted AppendEntries RPC from 4.
        Node 3 accepted AppendEntries RPC from 4.
        3 Stepping down.
        Node 3 accepted AppendEntries RPC from 4.
        Node 3 accepted AppendEntries RPC from 4.

* #### metadata
       Current Term: 10
       Commit Length: 3
       VotedFor: 3





### Client Interaction

A Raft cluster consists of followers, candidates, and a leader serving Raft clients. A Raft client stores the IP addresses and ports of all nodes and the current leader ID (which may get outdated). It sends GET/SET requests to the leader node, updates its leader ID if a failure occurs, and continues until a SUCCESS reply is received

### RPC and Protobuf

Communication between nodes requires two RPCs: AppendEntry and RequestVote, explained in detail in the [original Raft paper](https://raft.github.io/raft.pdf). These RPCs are modified for leader lease:

* AppendEntry RPC sends the lease interval duration when the leader starts the lease timer.
* RequestVoteReply RPC propagates the longest remaining duration of an old leader’s lease to the new candidate.

## Getting Started
To get a local copy of the code up and running, follow these steps.

### Prerequisites
* Basic understanding of Python 
* Python installed ([Download here](https://www.python.org/downloads/))
* gRPC ([Download here](https://grpc.io/))
* xterm
  ```sh
  sudo apt update
  sudo apt install xterm


### Installation
* Clone the repo
  
        git clone https://github.com/krishna21058/Raft.git
        chmmod +x run.sh         # (For linux users) run the sh file with asked parameters

For MacOS or Windows, you either manually start each node and client or modify the build file to automate running them locally.

## Deployment
### Remote Deployment

* Configure Google Cloud or Docker containers and adjust firewall settings to allow remote requests.
* node.py and client.py contain a static dictionary with all nodes' IP addresses and ports. This must be manually updated for gRPC communication.
* For local deployment, set all IP addresses to localhost.
* Give execute permissions to the .sh file and run it with the necessary parameters.

### Local Deployment

* Grant permission to the .sh file and run it with the required parameters.

### Running client file

* Run the client using python client.py and give commands in this format:

        SET Alice 5
        GET Alice
        SET Bob 1
        SET Alice 2  
        GET Alice

