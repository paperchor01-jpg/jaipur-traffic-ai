import asyncio, json, random
import torch, torch.nn as nn, torch.optim as optim
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI(title="Nexus AI - Emergency Protocol")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==========================================
# 1. MULTI-AGENT BRAIN (Unchanged)
# ==========================================
class CorridorBrain(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(9, 128), nn.ReLU(), nn.Linear(128, 4))
    def forward(self, x): return self.fc(x)

model = CorridorBrain()
optimizer = optim.Adam(model.parameters(), lr=0.01)

@app.get("/")
async def get_dashboard(): return FileResponse("static/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("✅ DASHBOARD CONNECTED - EMERGENCY PROTOCOLS ACTIVE")
    
    main_wait = [0, 0, 0]; cross_wait = [0, 0, 0]
    last_action = 0; wave_score = 0
    
    # --- NEW: SHARED EVENT STATE ---
    system_events = {"ambulance": 0, "accident": 0}

    # Background task to listen for your button clicks
    async def listen_to_dashboard():
        try:
            while True:
                data = await websocket.receive_text()
                msg = json.loads(data)
                if msg.get("event") == "ambulance": system_events["ambulance"] = 12 # 12 sec override
                elif msg.get("event") == "accident": system_events["accident"] = 15 # 15 sec blockage
        except: pass

    listener_task = asyncio.create_task(listen_to_dashboard())
    
    try:
        while True:
            # 1. Simulate standard traffic flow
            platoon = random.randint(5, 15) if random.random() > 0.7 else random.randint(0, 3)
            state_main = [platoon, random.randint(2, 8), random.randint(2, 8)]
            state_cross = [random.randint(1, 5), random.randint(1, 5), random.randint(1, 5)]

            # --- NEW: APPLY ACCIDENT PHYSICS ---
            if system_events["accident"] > 0:
                state_main[1] += 30 # Massive artificial pileup at Jct 2
                system_events["accident"] -= 1

            # 2. AI calculates the best move
            input_tensor = torch.FloatTensor([
                state_main[0], state_main[1], state_main[2],
                state_cross[0], state_cross[1], state_cross[2],
                main_wait[0], main_wait[1], main_wait[2]
            ])
            q_values = model(input_tensor)
            action = torch.argmax(q_values).item()

            # --- NEW: APPLY AMBULANCE OVERRIDE ---
            if system_events["ambulance"] > 0:
                action = 0 # FORCE Action 0 (All Main Green) regardless of AI math
                system_events["ambulance"] -= 1
                wave_status = "🚨 AMBULANCE OVERRIDE"
                eff = 100
            elif system_events["accident"] > 0:
                wave_status = "💥 COLLISION AT JCT 2"
            else:
                wave_status = "🟢 SYNCHRONIZED" if action == 0 else "🟠 ADJUSTING"

            lights = [0, 0, 0] 
            if action == 1: lights = [0, 0, 1]
            elif action == 2: lights = [1, 0, 0]
            elif action == 3: lights = [1, 1, 1]

            # 3. Apply Penalties & Train AI (Only if no ambulance)
            penalty = 0
            if system_events["ambulance"] == 0:
                for i in range(3):
                    if lights[i] == 0: 
                        main_wait[i] = 0; cross_wait[i] += 1
                        penalty += state_cross[i] * (cross_wait[i] ** 1.5)
                    else: 
                        cross_wait[i] = 0; main_wait[i] += 1
                        penalty += state_main[i] * (main_wait[i] ** 1.5)

                if action == 0: wave_score += 1
                else: wave_score = 0
                reward = -penalty + (wave_score * 10)

                loss = nn.MSELoss()(q_values[action], torch.tensor(float(reward)))
                optimizer.zero_grad(); loss.backward(); optimizer.step()
                eff = int(100 - min(penalty/10, 99))

            # Send state to 3D UI
            await websocket.send_text(json.dumps({
                "lights": lights, 
                "wave_status": wave_status, 
                "efficiency": eff
            }))
            await asyncio.sleep(1.0) 

    except WebSocketDisconnect: pass
    except Exception as e: print(f"⚠️ Error: {e}")
    finally: listener_task.cancel()

if __name__ == "__main__": uvicorn.run(app, host="127.0.0.1", port=8000)