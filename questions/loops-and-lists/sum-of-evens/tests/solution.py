n = int(input())
nums = []
for _ in range(n):
    nums.append(int(input()))
total = 0
for x in nums:
    if x % 2 == 0:
        total += x
print(total)
