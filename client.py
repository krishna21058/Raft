import grpc
import node_pb2
import node_pb2_grpc

class RaftClient:
    def __init__(self, server_addresses):
        self.server_addresses = server_addresses
        self.curr_index = 0
        self.channel = None
        self.stub = None
        

    def connect_to_next_node(self):
        if self.channel:
            self.channel.close()
        self.curr_index = (self.curr_index + 1) % len(self.server_addresses)

    def serve_client(self, request, max_retries=9):
        retries = 0
        while retries < max_retries:
            try:
                print("Sending request to:", self.server_addresses[self.curr_index])
                self.channel = grpc.insecure_channel(self.server_addresses[self.curr_index])
                self.stub = node_pb2_grpc.RaftServiceStub(self.channel)
                print("Trying to connect to:", self.server_addresses[self.curr_index])
                response = self.stub.ServeClient(request)
                return response
            except KeyboardInterrupt:
                print("KeyboardInterrupt, Exiting...")
                exit(0)
            except:
                print("Connection failed, trying next node")
                self.connect_to_next_node()
                retries += 1
        print("Maximum retries reached. Exiting...")


def main():
    node_ips = ['34.70.228.40:50051', '35.193.190.224:50052', '34.71.75.56:50053', '34.135.218.39:50054', '35.226.130.79:50055']
    client = RaftClient(node_ips)
    
    while True:
        request=input("Enter Request: ")
        serve_request = node_pb2.ServeClientArgs(Request=request)
        
        response = client.serve_client(serve_request)

        
        if response:
            if response.Success == "False" and response.LeaderID != -1:
                print(response.LeaderID, client.curr_index)
                print("Leader changed to:", node_ips[response.LeaderID - 1])
                client.curr_index = response.LeaderID - 1
            if response.Success == "False" and response.LeaderID == -1:
                print("No leader found")
            print("Status:", response.Success, "Data:", response.Data,"Current Leader:",response.LeaderID)
        else:
            print("No current active node found")

if __name__ == "__main__":
    main()
