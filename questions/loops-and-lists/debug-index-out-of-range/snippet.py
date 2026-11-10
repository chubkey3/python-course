nums = [2, 5, 3, 8]
count = 0
for i in range(len(nums)):
    if nums[i + 1] > nums[i]:
        count = count + 1
print(count)
