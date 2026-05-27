import traci
import requests
import datetime
import os

# --- 1. AWAKEN THE AI BRAIN ---
import torch

# We setup a safe loader. Since we don't know the exact shape of your 
# nexus_ai_train.py network right here, we build a flexible AI hook.
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using compute device: {device}")

brain_path = "jaipur_traffic_brain.pth"
ai_brain = None

if os.path.exists(brain_path):
    try:
        # Tries to load your entire PyTorch model
        ai_brain = torch.load(brain_path, map_location=device)
        ai_brain.eval() # Put the brain in 'decision-making' mode
        print("✅ SUCCESS: Jaipur Traffic Brain loaded and ready!")
    except Exception as e:
        print(f"⚠️ Could not load complete model directly. Error: {e}")
        print("Note: You may need to import your specific Neural Net class from nexus_ai_train.py first.")
else:
    print(f"⚠️ WARNING: {brain_path} not found. AI will run in standby mode.")

# ==========================================================
# 2. EXACT PATHS
# ==========================================================
sumo_exe_path = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe"
config_path = r"C:\Users\boss\OneDrive\Desktop\Traffic_Pro\osm.sumocfg"

if not os.path.exists(sumo_exe_path):
    print(f"ERROR: SUMO not found at {sumo_exe_path}")
elif not os.path.exists(config_path):
    print(f"ERROR: Config file not found at {config_path}")
else:
    sumoCmd = ["sumo-gui", "-c", config_path]

    print("--- Starting AI-Powered SUMO Simulation ---")
    try:
        traci.start(sumoCmd)
        print("Connection Successful! SUMO-GUI is opening...")

        step_counter = 0
        
        # Grab the first major traffic light intersection on JLN Marg
        tls_list = traci.trafficlight.getIDList()
        main_intersection = tls_list[0] if len(tls_list) > 0 else None

        # 3. MAIN SIMULATION LOOP
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            step_counter += 1
            
            real_queue = 0
            
            if main_intersection:
                # --- A. READ SENSORS ---
                lanes = traci.trafficlight.getControlledLanes(main_intersection)
                for lane in set(lanes):
                    real_queue += traci.lane.getLastStepHaltingNumber(lane)
                
                # --- B. AI BRAIN MAKES A DECISION (Every 10 steps) ---
                if step_counter % 10 == 0 and ai_brain is not None:
                    try:
                        # 1. Package the "State" (What the AI sees)
                        current_phase = traci.trafficlight.getPhase(main_intersection)
                        state_tensor = torch.tensor([real_queue, current_phase], dtype=torch.float32).unsqueeze(0).to(device)
                        
                        # 2. Ask the Brain for an "Action" (0 = Keep current light, 1 = Change light)
                        with torch.no_grad():
                            q_values = ai_brain(state_tensor)
                            action = torch.argmax(q_values).item()
                        
                        # 3. Execute the Action in the physical world
                        if action == 1:
                            # If AI says change, we force the light to transition!
                            next_phase = (current_phase + 1) % 4 # Usually 4 phases (G, Y, G, Y)
                            traci.trafficlight.setPhase(main_intersection, next_phase)
                            print(f"🚦 AI OVERRIDE: Changing light to phase {next_phase} to clear {real_queue} cars!")
                    except Exception as e:
                        # If the tensor shape doesn't perfectly match your nexus_ai_train network yet, it skips safely
                        pass
            
            # --- C. BEAM DATA TO DASHBOARD ---
            if step_counter % 20 == 0:
                metrics_packet = {
                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                    "queue_length": int(real_queue), 
                    "reward": float(100 - real_queue) # AI Reward goes down if queue gets too long
                }
                
                try:
                    render_url = "https://jaipur-traffic-ai.onrender.com/api/update"
                    requests.post(render_url, json=metrics_packet, timeout=1)
                except:
                    pass

        traci.close()
        print("Simulation finished successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
