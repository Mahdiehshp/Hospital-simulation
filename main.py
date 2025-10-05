from simulation import HospitalSimulation

if __name__ == "__main__":
    #doing the simulaton for 30 days
    sim = HospitalSimulation(simulation_end_time=43200)
    trace_df = sim.run()
    
    print("SIMULATION COMPLETED SUCCESSFULLY")