n = int(input())
nums = []
for i in range(n):
    nums.append(int(input()))
i = 0
while i < n:
    if nums[i] < 0:
        break
    print(nums[i])
    i += 1
print("done")
