# Fix the bugs: neighbours that add to 10
# Count how many pairs nums[i], nums[i + 1] add up to 10.
# This program has 2 bugs. Find them and fix them.
#
# Click "Save & Grade" to run the tests.

n = int(input())
nums = []
for i in range(n):
    nums.append(int(input()))

for i in range(n):
    if nums[i] + nums[i + 1] == 10:
        count = count + 1
print(count)
