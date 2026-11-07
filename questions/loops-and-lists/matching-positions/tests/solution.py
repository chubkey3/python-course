n = int(input())
a = []
for _ in range(n):
    a.append(int(input()))
b = []
for _ in range(n):
    b.append(int(input()))
count = 0
for i in range(n):
    if a[i] == b[i]:
        count += 1
print(count)
