
import grpc
from concurrent import futures
import node_pb2 as node
import node_pb2_grpc
import time
import threading
import random
import os

class RaftNodeImplementation(node_pb2_grpc.RaftServiceServicer):
    def __init__(self, node_id, port, node_ips, lease_duration=100):
        self.node_id = node_id
        self.currTerm = 0
        self.votedFor = None
        self.votedForTerm ={}
        self.log = []
        self.commitLength = 0
        self.currRole = "Follower"
        self.currLeader = -1
        self.votesReceived = set()
        self.sentLength = {}
        self.ackedLength = {}
        self.logs_updated = 0
        self.lease_duration = 0
        # self.lease_timer = None
        self.election_timer = random.randint(5,10)
        self.heartbeat_interval = 1
        self.ip = "localhost"
        self.port = port
        self.node_ip = f"localhost:{port}"
        self.node_ips = node_ips
        self.data = {}
        self.commitIndex=0
        self.appliedIndex=0

        self.election_timer_thread = threading.Thread(target=self.run_election_timer)
        self.election_timer_thread.daemon = True
        self.election_timer_thread.start()
        
        self.lease_timer_thread = threading.Thread(target=self.run_lease_timer)
        self.lease_timer_thread.daemon = True
        self.lease_timer_thread.start()

        self.heartbeat_thread = None
        if self.currRole == "Leader":
            self.start_heartbeat_thread()

    def run_lease_timer(self):
        while True:
            if(self.currLeader !=-1):
                self.start_lease_timer()
                time.sleep(1)

    def start_lease_timer(self):
        #if(self.currRole == "Leader"): 
        while self.lease_duration > 0:
            time.sleep(1)
            self.lease_duration -= 1
            print(f"Node {self.node_id} Lease Duration: {self.lease_duration} seconds. Election Timer: {self.election_timer} seconds.")
        if(self.lease_duration == 0):
            with open (f"logs_node_{self.node_id}/dump.txt", "a") as f:
                f.write(f"Leader {self.node_id} lease renewal failed. Stepping Down.\n")
            f.close()
            self.become_follower()
            # self.start_election()

    def become_follower(self):
        self.currRole = "Follower"
        self.currLeader= -1
        with open(f"logs_node_{self.node_id}/dump.txt", "a") as f:
            f.write(f"{self.node_id} Stepping down.\n")
        f.close()
        print(f"Node {self.node_id} became Follower after lease timeout.")
        
    def updateLogs(self):
        if self.currLeader != -1:
            try:
                leader_ip = self.node_ips[self.currLeader]
                channel = grpc.insecure_channel(leader_ip)
                stub = node_pb2_grpc.RaftServiceStub(channel)
                last_log_index = len(self.log) - 1
                last_log_term = self.log[last_log_index]['term'] if self.log else 0
                request = node.LogReplicationRequest(
                    node_id=self.node_id,
                    last_log_index=last_log_index,
                    last_log_term=last_log_term
                )
                response = stub.ReplicateLogs(request)

                for log_entry in response.log_entries:
                    # print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$", log_entry)
                    if self.validate_log_entry(log_entry):  # Check log consistency
                        self.apply_log_entry(log_entry)
                    else:
                        # Log inconsistency detected, handle accordingly
                        print(f"Log inconsistency detected for entry {log_entry.index} in log replication from leader.")
                        # Possible actions: request leader to resend logs, perform snapshot, etc.

                print(f"Node {self.node_id} logs updated successfully.")
            except Exception as e:
                print(f"Failed to update logs from leader: {e}")

    def validate_log_entry(self, log_entry):
        if log_entry.index < len(self.log):
            # Check if the log entry term matches with the current term in the follower's log
            return self.log[log_entry.index]['term'] == log_entry.term
        else:
            # If the log entry index is beyond the follower's log, it's considered consistent
            return True

    def apply_log_entry(self, log_entry):
        if log_entry.index >= len(self.log):
            self.log.extend([None] * (log_entry.index - len(self.log) + 1))
        self.log[log_entry.index] = {
            'term': log_entry.term,
            'key': log_entry.key,
            'operation': log_entry.operation,
            'value': log_entry.value,
            'index': log_entry.index
        }
        # Write the log entry to the log file
        if(log_entry.operation=="SET"):
            with open(f"logs_node_{self.node_id}/logs.txt", "a") as f:
                f.write(f"{self.log[log_entry.index]['operation']} {self.log[log_entry.index]['key']} {self.log[log_entry.index]['value']} {self.log[log_entry.index]['term']}\n")
            f.close()
        else:
            with open(f"logs_node_{self.node_id}/logs.txt", "a") as f:
                f.write(f"{self.log[log_entry.index]['operation']} {self.log[log_entry.index]['term']}\n")
            f.close()



    def ReplicateLogs(self, request, context):
        print(f"Node {self.node_id} received LogReplicationRequest from Node {request.node_id}.")
        last_log_index = request.last_log_index
        last_log_term = request.last_log_term
        log_entries = []
        for index, entry in enumerate(self.log[last_log_index + 1:], start=last_log_index + 1):
            log_entry = node.LogEntry(
                index=index,
                term=entry['term'],
                key=entry['key'],
                operation=entry['operation'],
                value=entry['value']
            )
            log_entries.append(log_entry)
        response = node.LogReplicationResponse(log_entries=log_entries)
        return response

    def run_election_timer(self):
        while True:
            if self.currRole in ["Follower", "Candidate"]:
                self.start_election_timer()
            time.sleep(1)

    def start_heartbeat_thread(self):
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_thread_func)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

    def heartbeat_thread_func(self):
        while self.currRole == "Leader":
            self.send_heartbeats()
            time.sleep(self.heartbeat_interval)

    def start_election(self):
        print("<--------------- starting election ------------------>")

        if self.currRole == "Leader":
            return

        if self.lease_duration!=0 or self.election_timer!=0:
            return

        self.currTerm += 1
        self.currRole = "Candidate"
        self.votedFor = self.node_id
        self.votedForTerm[self.currTerm]=self.node_id
        with open(f"logs_node_{self.node_id}/metadata.txt", "w") as f:
            f.write(f"Current Term: {self.currTerm}\nCommit Length: {self.commitLength}\nVotedFor: {self.votedFor}\n")
        f.close()
        self.votesReceived.add(self.node_id)
        self.lastTerm = self.log[-1].get('term', 0) if self.log else 0
        temp=self.lease_duration
        for i in self.node_ips.values():
            if i != self.node_ip:
                try:
                    channel = grpc.insecure_channel(i)
                    stub = node_pb2_grpc.RaftServiceStub(channel)
                    request = node.RequestVoteRequest(term=self.currTerm, candidate_id=self.node_id,
                                                      last_log_index=len(self.log) - 1, last_log_term=self.lastTerm)
                    response = stub.RequestVote(request)
                    if response.vote_granted:
                        self.votesReceived.add(i)
                    temp=max(temp,response.lease_duration)
                except Exception as e:
                    print(f"Node {self.node_id} failed to send or receive RequestVote RPC to/from Node {i}. Error:{e}")
                    with open(f"logs_node_{self.node_id}/dump.txt", "a") as f:
                        f.write(f"Error occurred while sending RPC to Node {i}.\n")
                    f.close()
                    continue

    
        self.check_votes(temp)
        self.election_timer = random.randint(5,10)

    def check_votes(self, oldLeaseWaitTimer):
        if len(self.votesReceived) >= (len(self.node_ips)+1 ) // 2:
            with open (f"logs_node_{self.node_id}/dump.txt", "a") as f:
                f.write(f"New Leader waiting for Old Leader Lease to timeout.\n")
            f.close()
            self.waitForOldLease(oldLeaseWaitTimer)
            print(f"Node {self.node_id} received majority votes. Transitioning to Leader.")
            self.become_leader()
        else:
            print(f"Node {self.node_id} did not receive majority votes yet.")
            self.currRole = "Follower"
            self.election_timer = random.randint(5,10)

    def waitForOldLease(self, oldLeaseWaitTimer):
        time.sleep(oldLeaseWaitTimer)

    def start_election_timer(self):
        while self.election_timer > 0:
            time.sleep(1)
            self.election_timer -= 1
        if(self.election_timer==0):
            with open(f"logs_node_{self.node_id}/dump.txt", "a") as f:
                f.write(f"Node {self.node_id} election timer timed out, Starting election.\n")
            f.close()
            if self.currRole == "Follower" and self.lease_duration==0:
                self.start_election()


    def send_heartbeats(self):
        majority_count = (len(self.node_ips)+1)//2
        received_heartbeats = 0  
        # self.lease_duration = 10
        with open(f"logs_node_{self.node_id}/dump.txt", "a") as f:
            f.write(f"Leader {self.node_id} sending heartbeat & Renewing Lease.\n")
        f.close()

        for node_id, follower in self.node_ips.items():
            if follower != self.node_ip:
                print(f"Node {self.node_id} sending heartbeat to Node {follower}.")
                try:
                    channel = grpc.insecure_channel(follower)
                    stub = node_pb2_grpc.RaftServiceStub(channel)
                    prev_log_index = self.sentLength.get(follower, 0) - 1
                    prev_log_term = self.log[prev_log_index].get('term', 0) if prev_log_index >= 0 else 0
                    request = node.AppendEntriesRequest(
                        term=self.currTerm,
                        leader_id=self.node_id,
                        prev_log_index=prev_log_index,
                        prev_log_term=prev_log_term,
                        entries=[],
                        leader_commit=self.commitLength,
                        lease_duration=self.lease_duration
                    )
                    response = stub.AppendEntries(request)
                    print(f"Node {self.node_id} received heartbeat response from Node {follower}.")
                    if response.success == "True":
                        self.ackedLength[follower] = self.sentLength[follower]
                        received_heartbeats += 1 
                    if response.currTerm > self.currTerm:
                        self.transition_to_follower(response.currTerm)
                        return 

                    elif response.success=="False" and response.currTerm==self.currTerm and self.currRole=="Leader" and self.lease_duration==0 and self.sentLength[follower]>0:
                        if dump_log_repl()==False :
                            continue
                        #send request for updating logs here
                        channel = grpc.insecure_channel(follower)
                        stub = node_pb2_grpc.RaftServiceStub(channel)
                        prev_log_index = self.sentLength.get(follower, 0) - 1
                        prev_log_term = self.log[prev_log_index].get('term', 0) if prev_log_index >= 0 else 0
                        request = node.AppendEntriesRequest(
                            term=self.currTerm,
                            leader_id=self.node_id,
                            prev_log_index=prev_log_index,
                            prev_log_term=prev_log_term,
                            entries=self.log,
                            leader_commit=self.commitLength,
                            lease_duration=self.lease_duration
                        )
                        response=stub.AppendEntries(request)
                except Exception as e:
                    print(f"Node {self.node_id} failed to send or receive heartbeat to/from Node {follower}.")
                    with open(f"logs_node_{self.node_id}/dump.txt", "a") as f:
                        f.write(f"Error occurred while sending RPC to Node {follower}.\n")
                    f.close()
                    continue

        if (received_heartbeats+1) >= majority_count:
            self.lease_duration = 10  

        self.election_timer = random.randint(5, 10)


    def AppendEntries(self, request, context):
        print(f"Node {self.node_id} received AppendEntries RPC from Node {request.leader_id}.")
        if request.term > self.currTerm:
            self.currTerm = term
            self.currRole = "Follower"
        
        self.currLeader = request.leader_id
        if self.currRole == "Leader":
            self.restart_lease_timer()
            response = node.AppendEntriesResponse(currTerm=self.currTerm, success="True")
            return response

        if (self.logs_updated == 0):
            self.logs_updated = 1
            self.updateLogs()
            response = node.AppendEntriesResponse(currTerm=self.currTerm, success="False")
            if request.term >= self.currTerm:
                self.currTerm = request.term
                self.currRole = "Follower"
                response.currTerm = self.currTerm
                response.success = "True"
                self.ackedLength[request.leader_id] = len(self.log)
                with open(f"logs_node_{self.node_id}/dump.txt", "a") as f:
                    f.write(f"Node {self.node_id} accepted AppendEntries RPC from {request.leader_id}.\n")
            
            else:
                with open(f"logs_node_{self.node_id}/dump.txt", "a") as f:
                    f.write(f"Node {self.node_id} rejected AppendEntries RPC from {request.leader_id}.\n") 
                response = node.AppendEntriesResponse(currTerm=self.currTerm, success="False")
                return response


            if request.lease_duration > self.lease_duration:
                self.lease_duration = request.lease_duration
            
            if request.leader_commit > self.commitLength:
                self.commitLength = min(request.leader_commit, len(self.log))
                self.commitIndex=self.commitLength
                self.appliedIndex=self.commitLength
                with open (f"logs_node_{self.node_id}/metadata.txt", "w") as f:
                    f.write(f"Current Term: {self.currTerm}\nCommit Length: {self.commitLength}\nVotedFor: {self.votedFor}\n")
                self.commit_log_entries()
            self.election_timer = random.randint(5,10)
            return response

        elif (self.logs_updated==-1):
            self.log=request.log
           
            for log_entry in self.log:
                if(log_entry.operation=="SET"):
                    with open(f"logs_node_{self.node_id}/logs.txt", "a") as f:
                        f.write(f"{self.log[log_entry.index]['operation']} {self.log[log_entry.index]['key']} {self.log[log_entry.index]['value']} {self.log[log_entry.index]['term']}\n")
                    f.close()
                else:
                    with open(f"logs_node_{self.node_id}/logs.txt", "a") as f:
                        f.write(f"{self.log[log_entry.index]['operation']} {self.log[log_entry.index]['term']}\n")
                    f.close()
            self.logs_updated=2
    
        elif (len(self.log)<request.prev_log_index and self.log[request.prev_log_index]['term']!=request.prev_log_term):
            self.updateLogs()
            self.currTerm = request.term
            self.currRole = "Follower"
            self.votedFor = None
            response = node.AppendEntriesResponse(currTerm=self.currTerm, success="True")
            return response

        else: 
            response = node.AppendEntriesResponse(currTerm=self.currTerm, success="False")
            if request.term >= self.currTerm:
                self.currTerm = request.term
                self.currRole = "Follower"
                response.currTerm = self.currTerm
                response.success = "True"
                self.ackedLength[request.leader_id] = len(self.log)
                with open(f"logs_node_{self.node_id}/dump.txt", "a") as f:
                    f.write(f"Node {self.node_id} accepted AppendEntries RPC from {request.leader_id}.\n")
            else:
                with open(f"logs_node_{self.node_id}/dump.txt", "a") as f:
                    f.write(f"Node {self.node_id} rejected AppendEntries RPC from {request.leader_id}.\n")
                response = node.AppendEntriesResponse(currTerm=self.currTerm, success="False")
                return response
            if len(request.entries) > 0:
                for entry in request.entries:
                    self.apply_entry(entry)


            if request.lease_duration > self.lease_duration:
                self.lease_duration = request.lease_duration
            
            if request.leader_commit > self.commitLength:
                self.commitLength = min(request.leader_commit, len(self.log))
                with open (f"logs_node_{self.node_id}/metadata.txt", "w") as f:
                    f.write(f"Current Term: {self.currTerm}\nCommit Length: {self.commitLength}\nVotedFor: {self.votedFor}\n")
                self.commit_log_entries()
            self.election_timer = random.randint(5,10)
            return response


    def RequestVote(self, request, context):
        
            print(f"Node {self.node_id} received RequestVote RPC from Node {request.candidate_id} for term {request.term}.")
            if request.term > self.currTerm:
                print(f"Node {self.node_id} transitioning to follower for term {request.term}.")
                self.transition_to_follower(request.term)
            lastTerm = self.log[-1].get('term', 0) if self.log else 0
            logOk = (request.last_log_term > lastTerm) or (request.last_log_term == lastTerm and request.last_log_index >= len(self.log) - 1)
            if request.term == self.currTerm and logOk and self.votedFor in {request.candidate_id, None} and self.currRole == "Follower":
                
                self.votedFor = request.candidate_id

                with open(f"logs_node_{self.node_id}/metadata.txt", "w") as f:
                    f.write(f"Current Term: {self.currTerm}\nCommit Length: {self.commitLength}\nVotedFor: {self.votedFor}\n")
                f.close()
                with open(f"logs_node_{self.node_id}/dump.txt", "a") as f:
                    f.write(f"Vote granted for Node {request.candidate_id} in term {request.term}.\n")
                f.close()
                print(f"Node {self.node_id} voted for Node {request.candidate_id} for term {request.term}.")
                self.election_timer = random.randint(5,10)

                print("-------------------------------------------")
                return node.RequestVoteResponse(term=self.currTerm, vote_granted=True, lease_duration=self.lease_duration)
            else:
                with open(f"logs_node_{self.node_id}/dump.txt", "a") as f:
                    f.write(f"Vote denied for Node {request.candidate_id} in term {request.term}.\n")
                f.close()
                print(f"Node {self.node_id} did not vote for Node {request.candidate_id} for term {request.term}.")
                return node.RequestVoteResponse(term=self.currTerm, vote_granted=False, lease_duration=self.lease_duration)

    def apply_entry(self, entry):
        if entry.operation == "GET":
            value = self.get(entry.key)
        elif entry.operation == "SET":
            self.log.append({'term': entry.term, 'operation': entry.operation, 'key': entry.key, 'value': entry.value, 'index': len(self.log)})
            # self.log_file.write(f"SET {entry.key} {entry.value} {entry.term}\n")
            with open(f"logs_node_{self.node_id}/logs.txt", "a") as f:
                f.write(f"SET {entry.key} {entry.value} {entry.term}\n")
            f.close()
            print(f"Node {self.node_id} added SET operation to log for key: {entry.key}, value: {entry.value}, index: {len(self.log)}") 
        else :
            self.log.append({'term': entry.term, 'operation': entry.operation, 'key': entry.key, 'value': entry.value, 'index': len(self.log)})
            # self.log_file.write(f"NO-OP {entry.term}\n")
            with open(f"logs_node_{self.node_id}/logs.txt", "a") as f:
                f.write(f"NO-OP {entry.term}\n")
            f.close()
            print(f"Node {self.node_id} added NO-OP operation to log for key: {entry.key}, value: {entry.value}, index: {len(self.log)}")

    def commit_log_entries(self):
        for i in range(len(self.log)):
            entry = self.log[i]
            if entry['operation'] == "SET":
                self.data[entry['key']] = entry['value']
                print(f"Node {self.node_id} committed SET operation for key: {entry['key']}, value: {entry['value']}")
                with open(f"logs_node_{self.node_id}/dump.txt", "a") as f:
                    f.write(f"Node {self.node_id} (follower) committed the entry {entry['operation']} to the state machine.\n")
                f.close()

    def get(self, key):
        return self.data[key] if key in self.data else None

    def ServeClient(self, request, context):
        msg=request.Request.split()
        if(msg[0]=="GET"):
            return self.ServeGet(msg[1])
        elif(msg[0]=="SET"):
            return self.ServeSet(msg[1],msg[2])


    def ServeGet(self, key):
        if(self.currRole!="Leader"):
            return node.ServeClientReply(Data="",Success="False",LeaderID=self.currLeader) 
        else:
            with open(f"logs_node_{self.node_id}/dump.txt", "a") as f:
                f.write(f"Node {self.node_id} (leader) received an GET request.\n")
            f.close()
            if(key not in self.data):
                return node.ServeClientReply(Data="",Success="False",LeaderID=self.currLeader)
            value = self.get(key)
            return node.ServeClientReply(Data=value,Success="True",LeaderID=self.currLeader)
            

    def ServeSet(self, key,value):
        # if(self.currRole!="Leader"):
        if(self.currRole!="Leader"):
            return node.ServeClientReply(Data="",LeaderID=self.currLeader,Success="False")
        else:
            with open(f"logs_node_{self.node_id}/dump.txt", "a") as f:
                f.write(f"Node {self.node_id} (leader) received an SET request.\n")
            f.close()

            log_entry = {'term': self.currTerm, 'operation': "SET", 'key': key, 'value': value, 'index': len(self.log)} #commit later?
            self.log.append(log_entry)
            # self.log_file.write(f"SET {key} {value} {self.currTerm}\n")
            with open(f"logs_node_{self.node_id}/logs.txt", "a") as f:
                f.write(f"SET {key} {value} {self.currTerm}\n")
            f.close()

            print(f"Node {self.node_id} added SET operation to log for key: {key}, value: {value}")
            checkmax=1
            for follower in self.node_ips.values():
                if follower != self.node_ip:
                    print(f"Node {self.node_id} sending LOG to Node {follower}.") 
                    if(self.replicate_log_entry(log_entry, self.node_id, follower) == "True"):
                        checkmax+=1
            if(checkmax>=(len(self.node_ips)+1)//2):
                if(log_entry['operation']=="NO-OP"):
                    return
                self.sentLength[follower] += 1
                self.ackedLength[follower] = self.sentLength[follower]
                self.data[log_entry['key']] = log_entry['value']
                self.commitLength += 1
                self.commitIndex=self.commitLength
                self.appliedIndex=self.commitLength
                with open (f"logs_node_{self.node_id}/dump.txt", "a") as f:
                    f.write(f"Node {self.node_id} (leader) committed the entry {log_entry['operation']} to the state machine.\n")
                f.close()
                # self.meta_file.write(f"Current Term: {self.currTerm}\n Commit Length{self.commitLength}\n VotedFor: {self.votedFor}\n")
                with open(f"logs_node_{self.node_id}/metadata.txt", "w") as f:
                    f.write(f"Current Term: {self.currTerm}\nCommit Length: {self.commitLength}\nVotedFor: {self.votedFor}\n")
                f.close()
       
            return node.ServeClientReply(Data="", Success="True", LeaderID=self.currLeader)

    def replicate_log_entry(self, log_entry, leader_id, follower_id):
        print(f"Node {self.node_id} sending AppendEntries RPC to Node {follower_id}.")
        try:
            channel = grpc.insecure_channel(follower_id)
            stub = node_pb2_grpc.RaftServiceStub(channel)
            prev_log_index = self.sentLength.get(follower_id, 0) - 1
            prev_log_term = self.log[prev_log_index]['term'] if prev_log_index >= 0 else 0
            request = node.AppendEntriesRequest(
                term=self.currTerm,
                leader_id=leader_id,
                prev_log_index=prev_log_index,
                prev_log_term=prev_log_term,
                entries=[log_entry],
                leader_commit=self.commitLength,
                lease_duration=self.lease_duration
            )
            response = stub.AppendEntries(request)
            print(f"Node {self.node_id} received AppendEntriesResponse RPC from Node {follower_id}.")

            if(response.currTerm > self.currTerm):
                self.transition_to_follower(response.currTerm)
                

            return response.success
        except Exception as e:
            print(
                f"Node {self.node_id} failed to send or receive AppendEntries RPC to/from Node {follower_id}.")
            with open(f"logs_node_{self.node_id}/dump.txt", "a") as f:
                f.write(f"Error occurred while sending RPC to Node {follower_id}.\n")
            f.close()

    def become_leader(self):
        self.currRole = "Leader"
        with open(f"logs_node_{self.node_id}/dump.txt", "a") as f:
            f.write(f"Node {self.node_id} became the leader for term {self.currTerm}.\n")
        f.close()
        self.currLeader = self.node_id
        self.lease_duration = 10
        print(f"Node {self.node_id} became Leader for term {self.currTerm}.")
        self.start_heartbeat_thread()
        log_entry = {'term': self.currTerm, 'operation': "NO-OP", 'key': "", 'value': "", 'index': len(self.log)}
        # self.log_file.write(f"NO-OP {self.currTerm}\n")

        with open(f"logs_node_{self.node_id}/logs.txt", "a") as f:
            f.write(f"NO-OP {self.currTerm}\n")
        f.close()

        self.log.append(log_entry)
        for follower in self.node_ips.values():

            if follower != self.node_ip:

                self.sentLength[follower] = len(self.log)
                self.ackedLength[follower] = 0
                self.sentLength[follower] = len(self.log)
                self.ackedLength[follower] = 0
                try:
                    channel = grpc.insecure_channel(follower)
                    stub = node_pb2_grpc.RaftServiceStub(channel)
                    prev_log_index = self.sentLength.get(follower, 0) - 1
                    prev_log_term = self.log[prev_log_index]['term'] if prev_log_index >= 0 else 0
                    log_entry = {'term': self.currTerm, 'operation': "NO-OP", 'key': "", 'value': "",'index': len(self.log)}


                    request = node.AppendEntriesRequest(
                        term=self.currTerm,
                        leader_id=self.node_id,
                        prev_log_index=prev_log_index,
                        prev_log_term=prev_log_term,
                        entries=[log_entry],
                        leader_commit=self.commitLength,
                        lease_duration=self.lease_duration
                    )
                    response = stub.AppendEntries(request)
                    if response.currTerm > self.currTerm:
                        self.transition_to_follower(response.currTerm)
                        return
                    print(f"Node {self.node_id} received AppendEntriesResponse RPC from Node {follower}.")
                except:
                    with open(f"logs_node_{self.node_id}/dump.txt", "a") as f:
                        f.write(f"Error occurred while sending RPC to Node {follower}.\n")
                    f.close()

    def transition_to_follower(self, term):
        self.currTerm = term
        self.currRole = "Follower"
        self.votedFor = None
        # self.meta_file.write(f"Current Term: {self.currTerm}\n Commit Length{self.commitLength}\n VotedFor: {self.votedFor}\n")
        with open(f"logs_node_{self.node_id}/metadata.txt", "w") as f:
            f.write(f"Current Term: {self.currTerm}\nCommit Length: {self.commitLength}\nVotedFor: {self.votedFor}\n")
        f.close()

    def dump_log_repl(self):
        return False

    def recover(self):
        try:
            if all(os.stat(f"logs_node_{self.node_id}/{file_name}").st_size == 0 for file_name in ["metadata.txt", "logs.txt", "dump.txt"]):
                return True  

            with open(f"logs_node_{self.node_id}/metadata.txt", "r") as f:
                lines = f.readlines()
                self.currTerm = int(lines[0].split(":")[1].strip())
                self.commitLength = int(lines[1].split(":")[1].strip())
                self.votedFor = int(lines[2].split(":")[1].strip())


            with open(f"logs_node_{self.node_id}/logs.txt", "r") as f:
                lines = f.readlines()
                for line in lines:
                    parts = line.split()
                    if parts[0] == "SET":
                        self.log.append({'term': int(parts[3]), 'operation': parts[0], 'key': parts[1], 'value': parts[2], 'index': len(self.log)})
                    else:
                        self.log.append({'term': int(parts[1]), 'operation': parts[0], 'key': "", 'value': "", 'index': len(self.log)})

            with open(f"logs_node_{self.node_id}/dump.txt", "a") as f:
                f.write(f"Node {self.node_id} recovered successfully.\n")
            print(f"Node {self.node_id} recovered successfully. !!!!")

        except FileNotFoundError:
            return True  
        except Exception as e:
        
            # with open(f"logs_node_{self.node_id}/dump.txt", "a") as f:
            #     f.write(f"Node {self.node_id} recovery failed: {str(e)}")
            print(f"Node {self.node_id} recovery failed: {str(e)} xxxxx")

        return False  

    def reset_all_files(self):
        with open(f"logs_node_{self.node_id}/metadata.txt", "w") as f:
            f.write("")
        with open(f"logs_node_{self.node_id}/logs.txt", "w") as f:
            f.write("")
        with open(f"logs_node_{self.node_id}/dump.txt", "w") as f:
            f.write("")

if  __name__ == '__main__':
    node_id = int(input("Enter the node id: "))
    # port = int(input("Enter the port number: "))
    node_ips = {1:'34.70.228.40:50051', 2:'35.193.190.224:50052', 3:'34.71.75.56:50053',4: '34.135.218.39:50054', 5:'35.226.130.79:50055'}
    port=int(node_ips[node_id].split(":")[1])
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    raft_node = RaftNodeImplementation(node_id, port, node_ips) 
    node_pb2_grpc.add_RaftServiceServicer_to_server(raft_node, server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()


    raft_node.recover()

   
        
    while True:
        time.sleep(5)
        print("---------------------------------------------------")
        print(f"Node {node_id} is {raft_node.currRole} for term {raft_node.currTerm}.")
        print("Logs: ")
        for i in raft_node.log:
            print(i)
        print("Data: ")
        for(i, j) in raft_node.data.items():
            print(f"Key: {i}, Value: {j}")
        print(f"Current Lease Duration: {raft_node.lease_duration} seconds.")
        print(f"Current Election Timer: {raft_node.election_timer} seconds.")
        print("---------------------------------------------------")

