import gc

before = gc.mem_free()
#---Place your code here---

import micropg_lite

#--------------------------
after = gc.mem_free()

print("\n\n\nFree Memory Before:               " + str(before) + " Bytes")
print("Free Memory After:                " + str(after) + " Bytes")

difference = before - after
print("The total usage of the script is: " + str(difference) + " Bytes")