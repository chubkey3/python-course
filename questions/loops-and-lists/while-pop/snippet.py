tasks = ["email", "report", "call"]
while len(tasks) > 0:
    removed = tasks.pop(0)
    print("Removed:", removed)
print(len(tasks))
