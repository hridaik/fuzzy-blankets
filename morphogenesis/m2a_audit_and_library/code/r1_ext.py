"""R1 extension (declared AFTER seeing 1/10 secondary individuals in a second shape class): secondary individuals 10-49 (std exp(2)), canonical clock."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
from r1_census import canon
if __name__ == "__main__":
    run_tasks([(canon, ("secondary", i)) for i in range(10, 50)], workers=4, label="R1-ext")
