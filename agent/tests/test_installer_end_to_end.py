import subprocess
import os
import time
import re

# We skip real QEMU end to end because in the docker container without KVM it's too slow and complex
# But wait! I can just write a wrapper script that uses local loop devices instead to simulate disk operations, OR use QEMU with a very small initrd.
