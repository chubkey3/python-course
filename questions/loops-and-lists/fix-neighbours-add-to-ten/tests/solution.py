n = int(input())
nums = []
for i in range(n):
    nums.append(int(input()))
count = 0
for i in range(n - 1):
    if nums[i] + nums[i + 1] == 10:
        count = count + 1
print(count)
