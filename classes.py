import random
import math


class Distributions:
    def __init__(self, seed=100):
        random.seed(seed)
        
    def uniform_dist(self, a, b):
        r = random.random()
        return a + int(r * (b - a + 1))
    
    def triangular_dist(self, min_val, mode, max_val):
        r = random.random()
        if r < (mode - min_val) / (max_val - min_val):
            return min_val + math.sqrt((mode - min_val) * (max_val - min_val) * r)
        else:
            return max_val - math.sqrt((max_val - mode) * (max_val - min_val) * (1 - r))
    
    def exponential_dist(self, mean_minutes):
        lambda_param = 1 / mean_minutes
        r = random.random()
        time_minutes = -math.log(r) / lambda_param
        return time_minutes
    
    def normal_dist(self, mu, sigma):
        r1 = random.random()
        r2 = random.random()
        z = math.sqrt(-2 * math.log(r1)) * math.cos(2 * math.pi * r2)
        return mu + sigma * z

dist = Distributions()

class powerout:
    count = 0
    def __init__(self):
        powerout.count += 1

    @classmethod
    def time(cls):
        r = dist.uniform_dist(1, 30)
        start_time = (cls.count * 30 + (r-1)) * 24 * 60
        finish_time = start_time + 24 * 60
        return start_time, finish_time

class Patient:
    id = 0
    def __init__(self):
        self.id = Patient.id
        Patient.id += 1

class NoneElective(Patient):
    def __init__(self):
        super().__init__()
        self.paperwork_time = 10
        self.in_lab_time = None
        self.before_surgery_time = None
        self.surgery_time = None
        self.surgery_type = None
        self.bedriddentime = None
        self.transfer_location = None

class Elective(Patient):
    def __init__(self):
        super().__init__()
        self.paperwork_time = 60
        self.in_lab_time = None
        self.before_surgery_time = None
        self.surgery_time = None
        self.surgery_type = None
        self.bedriddentime = None
        self.transfer_location = None

class Emergency:
    available_beds = 10
    queue = 0

class PreSurgery:
    available_beds = 50
    queue = 0

class Labratory:
    available_beds = 3
    queue = 0

class OperatingRoom:
    available_beds = 50
    queue = 0

class ICU:
    available_beds = 15
    queue = 0

class CCU:
    available_beds = 20
    queue = 0

class Ward:
    available_beds = 100
    queue = 0

class GroupEnterance:
    def __init__(self):
        self.number = dist.uniform_dist(2, 5)
        self.group_arrival_time = self.clock if hasattr(self, 'clock') else 0
        self.patients = []
        
        for _ in range(self.number):
            patient = NoneElective()
            patient.arrival_time = self.group_arrival_time
            self.patients.append(patient)
