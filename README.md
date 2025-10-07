# Hospital Simulation System

## Overview

This project simulates a hospital system consisting of seven departments to analyze patient flow, resource utilization, and operational efficiency.

## System Components

### Departments

The hospital consists of the following seven departments:

1. **Pre-operative Admission Ward** - 50 beds
2. **Emergency Department** - 10 beds
3. **Laboratory** - 3 beds (for conducting initial tests)
4. **Operating Rooms** - 50 beds (patient surgery)
5. **General Ward** - 100 beds (for patients with simple surgeries and after recovery of ICU and CCU patients)
6. **Intensive Care Unit (ICU)** - 15 beds (for patients with special conditions or complex surgeries)
7. **Cardiac Care Unit (CCU)** - 20 beds (for cardiac patients)

> **Note:** Resources are measured based on the number of available beds. 

## Patient Types

### Regular (Elective) Patients
- Scheduled surgery patients who visit their physician for diagnosis
- Admitted to pre-surgery ward **2 days before surgery**
- Represent **75%** of all patients
- Arrival rate: **1 patient per hour** (Poisson distribution)

### Emergency (Non-elective) Patients
- Require urgent/emergency surgery
- **Higher priority** than regular patients
- Immediate surgery if operating room is available
- Represent **25%** of all patients
- Arrival rate: **4 patients per hour** (Poisson distribution)
- **0.5%** arrive in groups due to mass casualty incidents
  - Group size: 2-5 people (discrete uniform distribution)
  - Maximum queue capacity: **10 patients** in ambulances

## Patient Flow

### Pre-surgery Process

#### Regular Patients
1. Admission to pre-operative ward
2. Wait **~60 minutes** for administrative work
3. Transfer to laboratory for testing
4. Return to bed for **2-day hospitalization**
5. Transfer to operating room

#### Emergency Patients
1. Admission to emergency department
2. Wait **~10 minutes** for administrative work
3. Transfer to laboratory for testing (priority over regular patients)
4. Return to emergency bed
5. Transfer to operating room

### Laboratory Testing
- Duration: **28-32 minutes** (uniform distribution)
- Emergency patients have priority
- Test waiting time for emergency patients: **5-100 minutes** (triangular distribution, mean: 75 minutes)

### Surgery Types

| Surgery Type | Probability | Description | Examples |
|--------------|-------------|-------------|----------|
| Simple | 50% | Basic procedures | Appendectomy |
| Moderate | 45% | Intermediate complexity | Cholecystectomy |
| Complex | 5% | High complexity procedures | Open-heart surgery |

- Operating room preparation time: **10 minutes** between surgeries
- Surgery duration: Follows distribution X with unique parameters per type

### Post-surgery Patient Routing

#### Simple Surgery
- Direct transfer to **General Ward**

#### Moderate Surgery
- **70%** → General Ward
- **10%** → ICU
- **20%** → CCU

#### Complex Surgery
- **10%** mortality rate → Morgue (outside system)
- **75%** non-cardiac → ICU
- **25%** cardiac → CCU

### Intensive Care (ICU/CCU)
- Recovery period: **Exponential distribution** (λ = 25 hours)
- **1%** probability of acute condition requiring repeat surgery
- Patients requiring repeat surgery treated as emergency patients
- After recovery: Transfer to General Ward

### General Ward
- Hospitalization duration: **Exponential distribution** (λ = 50 hours)
- Final step before discharge

## System Constraints

### Power Outages
- Frequency: **1 day per month** (random)
- Backup generators:
  - **100%** coverage for Operating Rooms
  - **80%** coverage for ICU and CCU beds

## Performance Metrics

The simulation tracks the following key performance indicators:

### Patient Flow Metrics
- Average time spent in the system
- Maximum and average queue length for:
  - Pre-operative ward
  - Laboratory
  - Operating room
  - Intensive care units
- Maximum and average waiting time in queues (all departments)

### System Capacity Metrics
- Probability of emergency queue capacity being full
- Average utilization rate of beds in each department

### Clinical Metrics
- Average number of repeat operations for patients with complex surgery

## Assumptions and Simplifications

- Patient admission details are omitted from analysis
- Patient deterioration from General Ward to ICU is disregarded due to rarity

---

## Project Information

This simulation model helps analyze hospital operations, identify bottlenecks, and optimize resource allocation across departments.
