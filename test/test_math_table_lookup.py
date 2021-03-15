#Performance improvement test environment
#Math table lookup
#Attempting to reduce the number of times the math function is called by using a lookup table with predefined values
#Tait Reid
#24-03-2020

import math
import time

class Before:
    MAX_CIRCLE_POSITIONS = 10
      
    def __init__(self):
        self.x = 0
        self.y = 0
        self.next_position_angle = 0

    def get_placement_position(self):
        self.next_position_angle += 1
        angle = float(self.next_position_angle)*float(360/Before.MAX_CIRCLE_POSITIONS)
        if angle >= 360:
            angle = 0
            self.next_position_angle = 0
            
        angle = math.radians(angle)
        x = self.x + 40*math.cos(angle)
        y = self.y + 40*math.sin(angle)
        return x, y
#==============================================================================            

class After:
    MAX_CIRCLE_POSITIONS = 10
      
    def __init__(self):
        self.x = 0
        self.y = 0
        self.next_position_angle = 0
        self.angles = []
        for a in range(After.MAX_CIRCLE_POSITIONS):
            self.next_position_angle += 1
            angle = float(self.next_position_angle)*float(360/After.MAX_CIRCLE_POSITIONS)
            if angle >= 360:
                angle = 0
                self.next_position_angle = 0
            angle = math.radians(angle)
            self.angles.append((40*math.cos(angle),40*math.sin(angle)))

    def get_placement_position(self):
        if self.next_position_angle > 9:
            self.next_position_angle = 0
        ret = self.angles[self.next_position_angle]
        self.next_position_angle += 1
        return ret
#==============================================================================

OPS = 2500000

b_start_time = time.time()

b = Before()
b_out = []
for i in range(OPS):
    b_out.append(b.get_placement_position())

b_duration = time.time() - b_start_time
print("before:", b_duration)

a_start_time = time.time()

a = After()
a_out = []
for i in range(OPS):
    a_out.append(a.get_placement_position())

a_duration = time.time() - a_start_time
print("after:", a_duration)
if b_out == a_out:
    print("output for new implementation was identical")
    improve = b_duration/a_duration
    print("improvement factor:", improve)
else:
    print("error in computation")