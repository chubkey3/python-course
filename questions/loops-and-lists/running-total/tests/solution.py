n = int(input())
nums = []
for i in range(n):
    nums.append(int(input()))
total = 0
for i in range(n):
    total = total + nums[i]
    print(total)
