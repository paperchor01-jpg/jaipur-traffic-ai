# ==============================================================================
# Project: Nexus AI - Digital Twin Traffic Synchronization
# Proprietary Software developed by Rupesh Yadav
# Copyright (c) 2026 Lifeera.in. All Rights Reserved.
# Unauthorized copying, modification, or distribution is strictly prohibited.
# ==============================================================================

import asyncio, json, random, time
import torch, torch.nn as nn, torch.optim as optim
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI(title="Nexus AI - Enterprise Demo")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==========================================
# 1. DEEP REINFORCEMENT LEARNING AI (THE BRAIN)
# ==========================================
class CorridorBrain(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(9, 128), nn.ReLU(), nn.Linear(128, 4))
    def forward(self, x): return self.fc(x)

model = CorridorBrain()
optimizer = optim.Adam(model.parameters(), lr=0.01)

# ==========================================
# 2. DETERMINISTIC SAFETY SUPERVISOR (THE GUARDIAN)
# ==========================================
class SafetySupervisor:
    def __init__(self):
        self.minimum_green_time = 4.0 # Seconds a light must stay green (prevents flicker)
        self.last_change_time = time.time()
        self.current_state = [0, 0, 0] 

    def evaluate_action(self, ai_suggested_action, system_events):
        current_time = time.time()
        time_since_last_change = current_time - self.last_change_time

        # RULE 1: AMBULANCE PREEMPTION (Absolute Priority)
        if system_events["ambulance"] > 0:
            self._update_state([0, 0, 0], current_time)
            return [0, 0, 0], "🚨 AMBULANCE PREEMPTION"

        # RULE 2: ACCIDENT REROUTING
        if system_events["accident"] > 0:
            self._update_state([1, 1, 1], current_time)
            return [1, 1, 1], "💥 COLLISION REROUTING"

        # RULE 3: AI SANITY CHECK
        proposed_lights = [0, 0, 0]
        if ai_suggested_action == 1: proposed_lights = [0, 0, 1]
        elif ai_suggested_action == 2: proposed_lights = [1, 0, 0]
        elif ai_suggested_action == 3: proposed_lights = [1, 1, 1]

        if proposed_lights != self.current_state and time_since_last_change < self.minimum_green_time:
            return self.current_state, "🛡️ SUPERVISOR HOLD"

        self._update_state(proposed_lights, current_time)
        wave_status = "🟢 AI SYNCHRONIZED" if ai_suggested_action == 0 else "🟠 AI ADJUSTING"
        return proposed_lights, wave_status

    def _update_state(self, new_lights, current_time):
        if new_lights != self.current_state:
            self.last_change_time = current_time
            self.current_state = new_lights

# ==========================================
# 3. WEBSOCKET SERVER & SIMULATION LOOP
# ==========================================
@app.get("/")
async def get_dashboard(): return FileResponse("static/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("✅ DASHBOARD CONNECTED")
    
    supervisor = SafetySupervisor()
    main_wait = [0, 0, 0]; cross_wait = [0, 0, 0]
    wave_score = 0; eff = 0
    static_main_wait = [0, 0, 0]; static_cross_wait = [0, 0, 0]
    static_last_change = time.time(); static_light_state = 0; static_eff = 0
    
    system_events = {"ambulance": 0, "accident": 0, "density": 1.0, "scenario": "live"}
    last_light_change = time.time()
    force_vertical_green = False

    async def listen_to_dashboard():
        try:
            while True:
                data = await websocket.receive_text()
                msg = json.loads(data)
                if msg.get("event") == "ambulance": system_events["ambulance"] = 12 
                elif msg.get("event") == "accident": system_events["accident"] = 15 
                elif msg.get("event") == "density": system_events["density"] = float(msg.get("value"))
                elif msg.get("event") == "scenario": system_events["scenario"] = msg.get("value")
                elif msg.get("event") == "stop":
                    system_events.update({"ambulance": 0, "accident": 0, "density": 1.0, "scenario": "live"})
                    await websocket.close()
                    break 
        except: pass

    listener_task = asyncio.create_task(listen_to_dashboard())
    
    try:
        while True:
            try:
                d_mult = system_events["density"]
                
                # --- HISTORICAL REAL-DATA SCENARIOS ---
                if system_events["scenario"] == "jln_rush_hour":
                    platoon = int(45 * d_mult)
                    state_main = [int(40 * d_mult), int(50 * d_mult), int(45 * d_mult)]
                    state_cross = [int(5 * d_mult), int(8 * d_mult), int(5 * d_mult)]
                elif system_events["scenario"] == "jln_accident_data":
                    platoon = int(10 * d_mult)
                    state_main = [int(15 * d_mult), int(65 * d_mult), int(10 * d_mult)] 
                    state_cross = [int(12 * d_mult), int(25 * d_mult), int(10 * d_mult)]
                else:
                    base_platoon = random.randint(8, 20) if random.random() > 0.6 else random.randint(2, 5)
                    platoon = int(base_platoon * d_mult)
                    state_main = [int(random.randint(3, 10) * d_mult), int(random.randint(3, 10) * d_mult), int(random.randint(3, 10) * d_mult)]
                    state_cross = [int(random.randint(2, 8) * d_mult), int(random.randint(2, 8) * d_mult), int(random.randint(2, 8) * d_mult)]

                # Add physical collision bottleneck to data
                if system_events["accident"] > 0: state_main[1] += 40 

                current_time = time.time()
                if current_time - last_light_change > 5.0:
                    force_vertical_green = not force_vertical_green
                    last_light_change = current_time

                # --- AI BRAIN SUGGESTION ---
                input_tensor = torch.FloatTensor([
                    state_main[0], state_main[1], state_main[2],
                    state_cross[0], state_cross[1], state_cross[2],
                    main_wait[0], main_wait[1], main_wait[2]
                ])
                q_values = model(input_tensor)
                ai_action = torch.argmax(q_values).item()
                if force_vertical_green and system_events["accident"] == 0 and system_events["ambulance"] == 0: ai_action = 3

                # --- SAFETY SUPERVISOR APPROVAL ---
                lights, wave_status = supervisor.evaluate_action(ai_action, system_events)

                if system_events["ambulance"] > 0: system_events["ambulance"] -= 1; eff = 100
                if system_events["accident"] > 0: system_events["accident"] -= 1

                # --- EFFICIENCY & LEARNING ---
                penalty = 0
                if system_events["ambulance"] == 0:
                    for i in range(3):
                        if lights[i] == 0: 
                            main_wait[i] = 0; cross_wait[i] += 1
                            penalty += state_cross[i] * (cross_wait[i] ** 1.3)
                        else: 
                            cross_wait[i] = 0; main_wait[i] += 1
                            penalty += state_main[i] * (main_wait[i] ** 1.3)
                    
                    wave_score += 2 if lights == [0, 0, 0] else -wave_score
                    reward = -penalty + (wave_score * 25) 
                    loss = nn.MSELoss()(q_values[ai_action], torch.tensor(float(reward)))
                    optimizer.zero_grad(); loss.backward(); optimizer.step()
                    eff = int(100 - min(penalty/20, 95))

                # --- GHOST STATIC TIMER (Control Group) ---
                if current_time - static_last_change > 30.0:
                    static_light_state = 1 - static_light_state; static_last_change = current_time
                static_penalty = 0
                for i in range(3):
                    if static_light_state == 0: 
                        static_main_wait[i] = 0; static_cross_wait[i] += 1; static_penalty += state_cross[i] * (static_cross_wait[i] ** 1.3)
                    else: 
                        static_cross_wait[i] = 0; static_main_wait[i] += 1; static_penalty += state_main[i] * (static_main_wait[i] ** 1.3)
                static_eff = int(100 - min(static_penalty/20, 95))

                await websocket.send_text(json.dumps({
                    "lights": lights, "wave_status": wave_status, "efficiency": eff, "static_efficiency": static_eff
                }))
                await asyncio.sleep(1.0) 

            except Exception as e:
                print(f"⚠️ GLITCH CAUGHT: {e}")
                await asyncio.sleep(1.0) 

    except WebSocketDisconnect: pass
    finally: listener_task.cancel()

if __name__ == "__main__": uvicorn.run(app, host="0.0.0.0", port=8000)