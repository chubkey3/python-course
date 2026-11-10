n = int(input())
nums = []
for i in range(n):
    nums.append(int(input()))
best = 0
for i in range(1, n):
    if nums[i] > nums[best]:
        best = i
print(nums[best])
print(best)
