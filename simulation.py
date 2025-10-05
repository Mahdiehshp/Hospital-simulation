import random
import math
import pandas as pd
import os
from classes import *

dist = Distributions()

def TransferFromOperatingroom(stype):
    if stype == "simple":
        d = "w"
    elif stype == "complex":
        r = random.random()
        if r <= 0.75:
            d = 'i'
        else:
            d = 'c'
    else:
        r = random.random()
        if r <= 0.70:
            d = 'w'
        elif 0.7 < r <= 0.8:
            d = 'i'
        else:
            d = 'c'
    return d
    
def death():
    r = random.random()
    if r <= 0.1:
        return 'death'
    else:
        return 'transfer'

class HospitalSimulation:
    def __init__(self, simulation_end_time=43200):
        self.clock = 0
        self.simulation_end_time = simulation_end_time
        self.future_event_list = []
        
        Emergency.available_beds = 10
        Emergency.queue = 0
        PreSurgery.available_beds = 50
        PreSurgery.queue = 0
        Labratory.available_beds = 3
        Labratory.queue = 0
        OperatingRoom.available_beds = 50
        OperatingRoom.queue = 0
        CCU.available_beds = 20
        CCU.queue = 0
        ICU.available_beds = 15
        ICU.queue = 0
        Ward.available_beds = 100
        Ward.queue = 0
        Patient.id = 0
        powerout.count = 0
        
        self.power_outages = []
        self.icu_reduced_capacity = False
        self.ccu_reduced_capacity = False
        
        self.queues = {
            'Emergency': [],
            'PreSurgery': [],
            'Laboratory': [],
            'OperatingRoom': [],
            'ICU': [],
            'CCU': [],
            'Ward': []
        }
        
        self.patients = {}
        self.trace_table = []
        self.step_counter = 0
        
        self.patient_stats = {}
        self.queue_stats = {dept: {'length': [], 'wait_time': []} for dept in self.queues.keys()}
        self.bed_utilization = {
            'Emergency': [],
            'PreSurgery': [],
            'Laboratory': [],
            'OperatingRoom': [],
            'ICU': [],
            'CCU': [],
            'Ward': []
        }
        self.emergency_full_count = 0
        self.emergency_check_count = 0
        self.resurgery_count = 0
        self.complex_surgery_count = 0
        self.last_clock = 0
    
    def record_trace(self, event_type, patient_id):
        self.step_counter += 1
        
        emergency_queue = len(self.queues['Emergency'])
        presurgery_queue = len(self.queues['PreSurgery'])
        lab_queue = len(self.queues['Laboratory'])
        or_queue = len(self.queues['OperatingRoom'])
        icu_queue = len(self.queues['ICU'])
        ccu_queue = len(self.queues['CCU'])
        ward_queue = len(self.queues['Ward'])
        
        emergency_busy = 10 - Emergency.available_beds
        presurgery_busy = 50 - PreSurgery.available_beds
        lab_busy = 3 - Labratory.available_beds
        or_busy = 50 - OperatingRoom.available_beds
        icu_busy = 15 - ICU.available_beds
        ccu_busy = 20 - CCU.available_beds
        ward_busy = 100 - Ward.available_beds
        
        emergency_wait = sum(self.clock - p['enter_time'] for p in self.queues['Emergency'])
        lab_wait = sum(self.clock - p['enter_time'] for p in self.queues['Laboratory'])
        or_wait = sum(self.clock - p['enter_time'] for p in self.queues['OperatingRoom'])
        icu_wait = sum(self.clock - p['enter_time'] for p in self.queues['ICU'])
        
        trace_entry = {
            'Step': self.step_counter,
            'Clock': round(self.clock, 2),
            'Event Type': event_type,
            'Patient ID': patient_id if patient_id else '',
            'Emergency Queue': emergency_queue,
            'PreSurgery Queue': presurgery_queue,
            'Lab Queue': lab_queue,
            'OR Queue': or_queue,
            'ICU Queue': icu_queue,
            'CCU Queue': ccu_queue,
            'Ward Queue': ward_queue,
            'Emergency Busy': emergency_busy,
            'PreSurgery Busy': presurgery_busy,
            'Lab Busy': lab_busy,
            'OR Busy': or_busy,
            'ICU Busy': icu_busy,
            'CCU Busy': ccu_busy,
            'Ward Busy': ward_busy,
            'Emergency Wait Time': round(emergency_wait, 2),
            'Lab Wait Time': round(lab_wait, 2),
            'OR Wait Time': round(or_wait, 2),
            'ICU Wait Time': round(icu_wait, 2),
            'FEL Size': len(self.future_event_list),
            'Next Event Time': round(self.future_event_list[0]['Event Time'], 2) if self.future_event_list else '',
            'Next Event Type': self.future_event_list[0]['Event Type'] if self.future_event_list else ''
        }
        
        self.trace_table.append(trace_entry)
    
    def schedule_event(self, event_type, event_time, patient_id=None, extra_data=None):
        event = {
            'Event Type': event_type,
            'Event Time': event_time,
            'Patient ID': patient_id,
            'Extra Data': extra_data or {}
        }
        self.future_event_list.append(event)
        self.future_event_list.sort(key=lambda x: x['Event Time'])
    
    def update_statistics(self):
        time_delta = self.clock - self.last_clock
        
        self.bed_utilization['Emergency'].append((time_delta, max(0, 10 - Emergency.available_beds)))
        self.bed_utilization['PreSurgery'].append((time_delta, max(0, 50 - PreSurgery.available_beds)))
        self.bed_utilization['Laboratory'].append((time_delta, max(0, 3 - Labratory.available_beds)))
        self.bed_utilization['OperatingRoom'].append((time_delta, max(0, 50 - OperatingRoom.available_beds)))
        self.bed_utilization['ICU'].append((time_delta, max(0, 15 - ICU.available_beds)))
        self.bed_utilization['CCU'].append((time_delta, max(0, 20 - CCU.available_beds)))
        self.bed_utilization['Ward'].append((time_delta, max(0, 100 - Ward.available_beds)))
        
        for dept_name, queue in self.queues.items():
            self.queue_stats[dept_name]['length'].append((time_delta, len(queue)))
        
        self.last_clock = self.clock
    
    def add_to_queue(self, department, patient_id, priority=False):
        self.queues[department].append({
            'patient_id': patient_id,
            'enter_time': self.clock,
            'priority': priority
        })
        self.queues[department].sort(key=lambda x: (not x['priority'], x['enter_time']))
    
    def remove_from_queue(self, department):
        if len(self.queues[department]) > 0:
            patient_entry = self.queues[department].pop(0)
            wait_time = self.clock - patient_entry['enter_time']
            self.queue_stats[department]['wait_time'].append(wait_time)
            return patient_entry['patient_id'], wait_time
        return None, 0
    
    def initialize(self):
        for month in range(int(self.simulation_end_time / (30 * 24 * 60)) + 1):
            powerout_event = powerout()
            start_time, finish_time = powerout.time()
            if start_time < self.simulation_end_time:
                self.schedule_event('Power Outage Start', start_time, None)
                self.schedule_event('Power Outage End', finish_time, None)
                self.power_outages.append((start_time, finish_time))
        
        first_elective_time = dist.exponential_dist(60)
        self.schedule_event('Elective Arrival', first_elective_time, None)
        
        first_nonelective_time = dist.exponential_dist(15)
        self.schedule_event('Non-Elective Arrival', first_nonelective_time, None)
        
        self.schedule_event('End of Simulation', self.simulation_end_time, None)
    
    def assign_patient_times(self, patient):
        patient.in_lab_time = dist.uniform_dist(28, 32)
        
        if patient.paperwork_time == 60:
            patient.before_surgery_time = 2 * 24 * 60
        else:
            patient.before_surgery_time = dist.triangular_dist(5, 75, 100)
        
        possibility = random.random()
        if possibility <= 0.50:
            patient.surgery_time = dist.normal_dist(30.22, 4.96)
            patient.surgery_type = "simple"
        elif possibility <= 0.95:
            patient.surgery_time = dist.normal_dist(67.09, 8.96)
            patient.surgery_type = "moderate"
        else:
            patient.surgery_time = dist.normal_dist(217.83, 56.95)
            patient.surgery_type = "complex"
        
        if patient.surgery_type == 'complex':
            if death() == 'death':
                patient.service = 'end'
                patient.bedriddentime = None
                patient.transfer_location = None
            else:
                location = TransferFromOperatingroom(patient.surgery_type)
                patient.transfer_location = location
                if location == 'w':
                    patient.bedriddentime = dist.exponential_dist(50*60)
                elif location == 'i':
                    patient.bedriddentime = dist.exponential_dist(25*60)
                else:
                    patient.bedriddentime = dist.exponential_dist(25*60)
        else:
            location = TransferFromOperatingroom(patient.surgery_type)
            patient.transfer_location = location
            if location == 'w':
                patient.bedriddentime = dist.exponential_dist(50*60)
            elif location == 'i':
                patient.bedriddentime = dist.exponential_dist(25*60)
            else:
                patient.bedriddentime = dist.exponential_dist(25*60)
    
    def process_elective_arrival(self, patient_id):
        patient = Elective()
        self.patients[patient.id] = patient
        self.assign_patient_times(patient)
        
        self.patient_stats[patient.id] = {
            'system_entry_time': self.clock,
            'arrival_time': self.clock,
            'departure_time': None,
            'patient_type': 'Elective',
            'surgery_type': patient.surgery_type,
            'current_location': None
        }
        
        next_arrival_time = self.clock + dist.exponential_dist(60)
        self.schedule_event('Elective Arrival', next_arrival_time, None)
        
        if PreSurgery.available_beds > 0:
            PreSurgery.available_beds -= 1
            self.patient_stats[patient.id]['current_location'] = 'PreSurgery'
            self.schedule_event('Paperwork Complete', self.clock + patient.paperwork_time, patient.id)
        else:
            self.add_to_queue('PreSurgery', patient.id, priority=False)
    
    def process_nonelective_arrival(self, patient_id):
        is_group = random.random() < 0.02
        if is_group:
            group = GroupEnterance()
            group.group_arrival_time = self.clock
            for patient in group.patients:
                self.emergency_check_count += 1
                total_emergency_load = (10 - Emergency.available_beds) + len(self.queues['Emergency'])
                if total_emergency_load >= 10:
                    self.emergency_full_count += 1
                    continue
                self.patients[patient.id] = patient
                self.assign_patient_times(patient)
                
                self.patient_stats[patient.id] = {
                    'system_entry_time': self.clock,
                    'arrival_time': self.clock,
                    'departure_time': None,
                    'patient_type': 'Group Non-Elective',
                    'surgery_type': patient.surgery_type,
                    'current_location': None
                }
                
                if Emergency.available_beds > 0:
                    Emergency.available_beds -= 1
                    self.patient_stats[patient.id]['current_location'] = 'Emergency'
                    self.schedule_event('Paperwork Complete', self.clock + patient.paperwork_time, patient.id)
                else:
                    self.add_to_queue('Emergency', patient.id, priority=True)
        else:
            self.emergency_check_count += 1
            total_emergency_load = (10 - Emergency.available_beds) + len(self.queues['Emergency'])
            if total_emergency_load >= 10:
                self.emergency_full_count += 1
            else:
                patient = NoneElective()
                self.patients[patient.id] = patient
                self.assign_patient_times(patient)
                
                self.patient_stats[patient.id] = {
                    'system_entry_time': self.clock,
                    'arrival_time': self.clock,
                    'departure_time': None,
                    'patient_type': 'Non-Elective',
                    'surgery_type': patient.surgery_type,
                    'current_location': None
                }
                
                if Emergency.available_beds > 0:
                    Emergency.available_beds -= 1
                    self.patient_stats[patient.id]['current_location'] = 'Emergency'
                    self.schedule_event('Paperwork Complete', self.clock + patient.paperwork_time, patient.id)
                else:
                    self.add_to_queue('Emergency', patient.id, priority=True)
        
        next_arrival_time = self.clock + dist.exponential_dist(15)
        self.schedule_event('Non-Elective Arrival', next_arrival_time, None)
    
    def process_paperwork_complete(self, patient_id):
        patient = self.patients[patient_id]
        
        if Labratory.available_beds > 0:
            Labratory.available_beds -= 1
            self.schedule_event('Lab Complete', self.clock + patient.in_lab_time, patient_id)
        else:
            self.add_to_queue('Laboratory', patient_id)
    
    def process_lab_complete(self, patient_id):
        patient = self.patients[patient_id]
        
        Labratory.available_beds += 1
        
        next_patient, _ = self.remove_from_queue('Laboratory')
        if next_patient:
            Labratory.available_beds -= 1
            next_patient_obj = self.patients[next_patient]
            self.schedule_event('Lab Complete', self.clock + next_patient_obj.in_lab_time, next_patient)
        
        self.schedule_event('Ready for Surgery', self.clock + patient.before_surgery_time, patient_id)
    
    def process_ready_for_surgery(self, patient_id):
        current_location = self.patient_stats[patient_id]['current_location']
        
        if OperatingRoom.available_beds > 0:
            OperatingRoom.available_beds -= 1
            
            if current_location == 'Emergency':
                Emergency.available_beds += 1
                next_patient, _ = self.remove_from_queue('Emergency')
                if next_patient:
                    Emergency.available_beds -= 1
                    self.patient_stats[next_patient]['current_location'] = 'Emergency'
                    next_patient_obj = self.patients[next_patient]
                    self.schedule_event('Paperwork Complete', self.clock + next_patient_obj.paperwork_time, next_patient)
                    
            elif current_location == 'PreSurgery':
                PreSurgery.available_beds += 1
                next_patient, _ = self.remove_from_queue('PreSurgery')
                if next_patient:
                    PreSurgery.available_beds -= 1
                    self.patient_stats[next_patient]['current_location'] = 'PreSurgery'
                    next_patient_obj = self.patients[next_patient]
                    self.schedule_event('Paperwork Complete', self.clock + next_patient_obj.paperwork_time, next_patient)
            
            self.patient_stats[patient_id]['current_location'] = 'OperatingRoom'
            self.start_surgery(patient_id)
        else:
            self.add_to_queue('OperatingRoom', patient_id)
    
    def start_surgery(self, patient_id):
        patient = self.patients[patient_id]
        
        if patient.surgery_type == 'complex':
            self.complex_surgery_count += 1
        
        self.schedule_event('Surgery End', self.clock + patient.surgery_time + 10, patient_id)
    
    def check_resurgery_needed(self, patient):
        if patient.surgery_type == "complex":
            r = random.random()
            if r <= 0.01:
                return True
        return False
    
    def process_surgery_end(self, patient_id):
        patient = self.patients[patient_id]
        
        if hasattr(patient, 'service') and patient.service == 'end':
            OperatingRoom.available_beds += 1
            self.check_or_queue()
            
            self.patient_stats[patient_id]['departure_time'] = self.clock
            self.patient_stats[patient_id]['current_location'] = 'Died'
            return
        
        if self.check_resurgery_needed(patient):
            self.resurgery_count += 1
            OperatingRoom.available_beds += 1
            self.check_or_queue()
            
            self.patient_stats[patient_id]['current_location'] = 'OperatingRoom'
            
            if OperatingRoom.available_beds > 0:
                OperatingRoom.available_beds -= 1
                self.start_surgery(patient_id)
            else:
                self.add_to_queue('OperatingRoom', patient_id)
            return
        
        OperatingRoom.available_beds += 1
        self.check_or_queue()
        
        location = patient.transfer_location
        
        if location == 'w':
            if Ward.available_beds > 0:
                Ward.available_beds -= 1
                self.patient_stats[patient_id]['current_location'] = 'Ward'
                self.schedule_event('Ward Discharge', self.clock + patient.bedriddentime, patient_id)
            else:
                self.add_to_queue('Ward', patient_id)
                self.patient_stats[patient_id]['current_location'] = 'Waiting for Ward'
                
        elif location == 'i':
            if ICU.available_beds > 0:
                ICU.available_beds -= 1
                self.patient_stats[patient_id]['current_location'] = 'ICU'
                self.schedule_event('ICU Discharge', self.clock + patient.bedriddentime, patient_id)
            else:
                self.add_to_queue('ICU', patient_id)
                self.patient_stats[patient_id]['current_location'] = 'Waiting for ICU'
                
        else:
            if CCU.available_beds > 0:
                CCU.available_beds -= 1
                self.patient_stats[patient_id]['current_location'] = 'CCU'
                self.schedule_event('CCU Discharge', self.clock + patient.bedriddentime, patient_id)
            else:
                self.add_to_queue('CCU', patient_id)
                self.patient_stats[patient_id]['current_location'] = 'Waiting for CCU'
    
    def process_discharge(self, patient_id, department):
        patient = self.patients[patient_id]
        
        if department == 'Ward':
            Ward.available_beds += 1
            next_patient, _ = self.remove_from_queue('Ward')
            if next_patient:
                Ward.available_beds -= 1
                self.patient_stats[next_patient]['current_location'] = 'Ward'
                next_patient_obj = self.patients[next_patient]
                self.schedule_event('Ward Discharge', self.clock + next_patient_obj.bedriddentime, next_patient)
            self.patient_stats[patient_id]['departure_time'] = self.clock
            self.patient_stats[patient_id]['current_location'] = 'Discharged'
        
        elif department == 'ICU':
            ICU.available_beds += 1
            if self.icu_reduced_capacity:
                max_available = int(15 * 0.8)
                if ICU.available_beds > max_available:
                    ICU.available_beds = max_available
            next_patient, _ = self.remove_from_queue('ICU')
            if next_patient:
                ICU.available_beds -= 1
                self.patient_stats[next_patient]['current_location'] = 'ICU'
                next_patient_obj = self.patients[next_patient]
                self.schedule_event('ICU Discharge', self.clock + next_patient_obj.bedriddentime, next_patient)
            if Ward.available_beds > 0 and self.queues['Ward']:
                Ward.available_beds -= 1
                ward_patient_id, _ = self.remove_from_queue('Ward')
                self.patient_stats[ward_patient_id]['current_location'] = 'Ward'
                ward_patient = self.patients[ward_patient_id]
                self.schedule_event('Ward Discharge', self.clock + ward_patient.bedriddentime, ward_patient_id)
            self.patient_stats[patient_id]['departure_time'] = self.clock
            self.patient_stats[patient_id]['current_location'] = 'Discharged'
        
        elif department == 'CCU':
            CCU.available_beds += 1
            if self.ccu_reduced_capacity:
                max_available = int(20 * 0.8)
                if CCU.available_beds > max_available:
                    CCU.available_beds = max_available
            next_patient, _ = self.remove_from_queue('CCU')
            if next_patient:
                CCU.available_beds -= 1
                self.patient_stats[next_patient]['current_location'] = 'CCU'
                next_patient_obj = self.patients[next_patient]
                self.schedule_event('CCU Discharge', self.clock + next_patient_obj.bedriddentime, next_patient)
            if Ward.available_beds > 0 and self.queues['Ward']:
                Ward.available_beds -= 1
                ward_patient_id, _ = self.remove_from_queue('Ward')
                self.patient_stats[ward_patient_id]['current_location'] = 'Ward'
                ward_patient = self.patients[ward_patient_id]
                self.schedule_event('Ward Discharge', self.clock + ward_patient.bedriddentime, ward_patient_id)
            self.patient_stats[patient_id]['departure_time'] = self.clock
            self.patient_stats[patient_id]['current_location'] = 'Discharged'
    
    def check_or_queue(self):
        next_patient, _ = self.remove_from_queue('OperatingRoom')
        if next_patient:
            next_location = self.patient_stats[next_patient]['current_location']
            OperatingRoom.available_beds -= 1
            if next_location == 'Emergency':
                Emergency.available_beds += 1
                waiting_patient, _ = self.remove_from_queue('Emergency')
                if waiting_patient:
                    Emergency.available_beds -= 1
                    self.patient_stats[waiting_patient]['current_location'] = 'Emergency'
                    waiting_patient_obj = self.patients[waiting_patient]
                    self.schedule_event('Paperwork Complete', self.clock + waiting_patient_obj.paperwork_time, waiting_patient)
            elif next_location == 'PreSurgery':
                PreSurgery.available_beds += 1
                waiting_patient, _ = self.remove_from_queue('PreSurgery')
                if waiting_patient:
                    PreSurgery.available_beds -= 1
                    self.patient_stats[waiting_patient]['current_location'] = 'PreSurgery'
                    waiting_patient_obj = self.patients[waiting_patient]
                    self.schedule_event('Paperwork Complete', self.clock + waiting_patient_obj.paperwork_time, waiting_patient)
            self.patient_stats[next_patient]['current_location'] = 'OperatingRoom'
            self.start_surgery(next_patient)
    
    def process_power_outage_start(self):
        self.icu_reduced_capacity = True
        self.ccu_reduced_capacity = True
        
        icu_max = int(15 * 0.8)
        ccu_max = int(20 * 0.8)
        
        if ICU.available_beds > icu_max:
            ICU.available_beds = icu_max
        if CCU.available_beds > ccu_max:
            CCU.available_beds = ccu_max
    
    def process_power_outage_end(self):
        self.icu_reduced_capacity = False
        self.ccu_reduced_capacity = False
    
    def run(self):
        self.initialize()
        
        while self.future_event_list and self.clock < self.simulation_end_time:
            current_event = self.future_event_list.pop(0)
            
            self.update_statistics()
            
            self.clock = current_event['Event Time']
            
            if self.clock >= self.simulation_end_time:
                break
            
            event_type = current_event['Event Type']
            patient_id = current_event['Patient ID']
            extra_data = current_event.get('Extra Data', {})
            
            self.record_trace(event_type, patient_id)
            
            if event_type == 'Elective Arrival':
                self.process_elective_arrival(patient_id)
            
            elif event_type == 'Non-Elective Arrival':
                self.process_nonelective_arrival(patient_id)
            
            elif event_type == 'Power Outage Start':
                self.process_power_outage_start()
            
            elif event_type == 'Power Outage End':
                self.process_power_outage_end()
            
            elif event_type == 'Paperwork Complete':
                self.process_paperwork_complete(patient_id)
            
            elif event_type == 'Lab Complete':
                self.process_lab_complete(patient_id)
            
            elif event_type == 'Ready for Surgery':
                self.process_ready_for_surgery(patient_id)
            
            elif event_type == 'Surgery End':
                self.process_surgery_end(patient_id)
            
            elif 'Discharge' in event_type:
                dept = event_type.split()[0]
                self.process_discharge(patient_id, dept)
        
        self.print_statistics()
        return self.create_trace_excel()
    
    def print_statistics(self):
        print("SIMULATION STATISTICS")
        
        total_time = 0
        completed_patients = 0
        for pid, data in self.patient_stats.items():
            if data['departure_time']:
                total_time += data['departure_time'] - data['system_entry_time']
                completed_patients += 1
        
        if completed_patients > 0:
            avg_time_in_system = total_time / completed_patients
            print(f"\n1. Average Time in System: {avg_time_in_system:.2f} minutes ({avg_time_in_system/60:.2f} hours)")
        
        if self.emergency_check_count > 0:
            prob_emergency_full = self.emergency_full_count / self.emergency_check_count
            print(f"\n2. Probability of Emergency Full: {prob_emergency_full:.4f} ({prob_emergency_full*100:.2f}%)")
        
        print(f"\n3. Queue Statistics by Department:")
        
        departments = ['PreSurgery', 'Laboratory', 'OperatingRoom', 'ICU', 'CCU', 'Ward']
        for dept in departments:
            max_queue = 0
            total_weighted_length = 0
            total_time = 0
            
            for time_delta, length in self.queue_stats[dept]['length']:
                max_queue = max(max_queue, length)
                total_weighted_length += time_delta * length
                total_time += time_delta
            
            avg_queue_length = total_weighted_length / total_time if total_time > 0 else 0
            
            wait_times = self.queue_stats[dept]['wait_time']
            avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0
            
            print(f"  {dept}:")
            print(f"    - Max Queue Length: {max_queue}")
            print(f"    - Avg Queue Length: {avg_queue_length:.2f}")
            print(f"    - Avg Wait Time: {avg_wait_time:.2f} minutes")
        
        if self.complex_surgery_count > 0:
            avg_resurgery = self.resurgery_count / self.complex_surgery_count
            print(f"\n4. Re-surgery Statistics:")
            print(f"   - Complex Surgeries: {self.complex_surgery_count}")
            print(f"   - Re-surgeries: {self.resurgery_count}")
            print(f"   - Avg Re-surgeries per Complex Surgery: {avg_resurgery:.4f}")
        
        print(f"\n5. Bed Utilization by Department:")
        
        bed_capacity = {
            'Emergency': 10,
            'PreSurgery': 50,
            'Laboratory': 3,
            'OperatingRoom': 50,
            'ICU': 15,
            'CCU': 20,
            'Ward': 100
        }
        
        for dept, capacity in bed_capacity.items():
            total_weighted_usage = 0
            total_time = 0
            
            for time_delta, beds_used in self.bed_utilization[dept]:
                total_weighted_usage += time_delta * beds_used
                total_time += time_delta
            
            avg_utilization = (total_weighted_usage / total_time / capacity * 100) if total_time > 0 else 0
            
            print(f"  {dept}: {avg_utilization:.2f}%")
    
    def create_trace_excel(self):
        df = pd.DataFrame(self.trace_table)
        
        excel_file = os.path.join(os.getcwd(), 'hospital_simulation_trace.xlsx')
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Trace Table', index=False)
            
            worksheet = writer.sheets['Trace Table']
            for idx, column in enumerate(df.columns):
                column_length = max(df[column].astype(str).map(len).max(), len(column))
                col_letter = chr(65 + idx) if idx < 26 else chr(65 + idx//26 - 1) + chr(65 + idx%26)
                worksheet.column_dimensions[col_letter].width = min(column_length + 2, 50)
        
        return df

