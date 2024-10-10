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

# micropg usage on pico w:       27456 Bytes
# micropg_lite usage on pico w:  10576 Bytes
# micropg_lite-V3 20.7.2024 usage pico w: 17440 Bytes
# micropg_lite-V3 10.10.2024 usage pico w: 15296 Bytes