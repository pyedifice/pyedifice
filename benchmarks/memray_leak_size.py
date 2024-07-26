#
# Print total leaked memory size in bytes from a memrary .bin file.
#
# https://github.com/bloomberg/memray/discussions/570#discussioncomment-8798447
#

import sys

from memray import FileReader

if len(sys.argv) < 2:
    print("Usage: python memray_leak_size.py <memray-bin-file>")
    sys.exit()

reader = FileReader(sys.argv[1])
leaked = sum(record.size for record in reader.get_leaked_allocation_records())
print(leaked)
