import os
import sys
import torch
import torch.nn as nn
import torch.optim as optim
import json # For dashboard data export

# --- 1. SETUP SUMO PATHS ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

import traci

# --- 2. THE AI BRAIN (Neural Network) ---
class TrafficBrain(nn.Module):
    def __init__(self, input_size, output_size):
        super(TrafficBrain, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_size, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, output_size) 
        )
    def forward(self, x):
        return self.fc(x)

# --- 3. THE TRAINING ENGINE ---
def run_nexus_training():
    
    # 🎯 YOUR EXACT JUNCTION ID
    TARGET_JUNCTION = "cluster_1753726593_2187740562" 
    
    # Start SUMO in GUI mode
    sumo_binary = "sumo-gui" 
    traci.start([sumo_binary, "-c", "osm.sumocfg", "--start"])

    # Initialize the Neural Network Brain
    model = TrafficBrain(input_size=4, output_size=2)
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss() # Used to calculate the AI's "mistakes"

    # Data storage for your web dashboard
    dashboard_data = []

    print(f"🚀 Nexus AI (Smart Version) taking control of JLN Marg Junction: {TARGET_JUNCTION}")

    step = 0
    # --- THE CORE AI LOOP ---
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        # The AI evaluates traffic every 10 simulation seconds
        if step % 10 == 0:
            try:
                # A. SENSE: Gather data from the junction
                controlled_lanes = traci.trafficlight.getControlledLanes(TARGET_JUNCTION)
                unique_lanes = list(set(controlled_lanes))
                
                # Count waiting cars on the incoming lanes
                waiting_counts = [traci.lane.getHaltingNumber(lane) for lane in unique_lanes[:4]]
                while len(waiting_counts) < 4: 
                    waiting_counts.append(0.0)
                
                state = torch.FloatTensor(waiting_counts)

                # B. THINK: AI predicts the best traffic light phase
                prediction = model(state)
                action = torch.argmax(prediction).item()

                # C. ACT: Change the physical light in the simulation
                new_phase = action * 2 
                traci.trafficlight.setPhase(TARGET_JUNCTION, new_phase)

                # D. LEARN: Reinforcement Learning Logic
                # Total waiting cars acts as a "Punishment" (Negative Reward)
                total_waiting = sum(waiting_counts)
                reward = -total_waiting 

                # Tell PyTorch what the target score should have been
                target = prediction.clone()
                target[action] = reward 

                # Calculate the mistake (Loss) and update the brain weights
                loss = criterion(prediction, target)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                # E. DASHBOARD EXPORT: Save live metrics for the website
                metrics = {
                    "time_step": step,
                    "waiting_cars": total_waiting,
                    "ai_loss": float(loss.item()),
                    "active_phase": new_phase
                }
                dashboard_data.append(metrics)

                # Write live data to a JSON file every 50 steps
                if step % 50 == 0:
                    with open("live_metrics.json", "w") as f:
                        json.dump(dashboard_data, f)
                    print(f"Step {step} | Waiting Cars: {total_waiting} | AI adjusting brain...")

                # F. CHAOS INJECTION: Simulate a vehicle breakdown
                if step == 500:
                    all_vehs = traci.vehicle.getIDList()
                    if len(all_vehs) > 0:
                        victim = all_vehs[0]
                        lane = traci.vehicle.getLaneID(victim)
                        traci.vehicle.setStop(victim, lane, pos=20, duration=500)
                        print(f"⚠️ ACCIDENT ALERT: Vehicle {victim} stalled on {lane}")

            except Exception as e:
                # Silently skip errors if lanes haven't fully loaded in the first fraction of a second
                if step > 0:
                    print(f"❌ Error at step {step}: {e}")

        step += 1
        # Stop simulation early just for fast training loops (can be increased later)
        if step > 2000: 
            break 

    # --- 4. SHUTDOWN & SAVE ---
    traci.close()
    torch.save(model.state_dict(), "jaipur_traffic_brain_smart.pth")
    print("✅ Smart Training complete. Data exported to 'live_metrics.json'.")

if __name__ == "__main__":
    run_nexus_training()