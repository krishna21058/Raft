nodes=[1,2,3,4,5]
for node in nodes:
    with open(f"logs_node_{node}/logs.txt", "w") as f:
        f.write("")
    f.close()
    with open(f"logs_node_{node}/dump.txt", "w") as f:
        f.write("")
    f.close()
    with open(f"logs_node_{node}/metadata.txt", "w") as f:
        f.write("")
    f.close()

    