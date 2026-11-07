n = int(input())
nums = []
for _ in range(n):
    nums.append(int(input()))
count = 0
for i in range(len(nums)):
    if nums[i] == i:
        count += 1
print(count)
