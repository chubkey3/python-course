n = int(input())
nums = []
for i in range(n):
    nums.append(int(input()))
count = 0
for i in range(1, n):
    if nums[i] > nums[i - 1]:
        count = count + 1
print(count)
