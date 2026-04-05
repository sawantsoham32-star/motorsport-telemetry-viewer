Motorsport Telemetry Viewer 🏎️

A MoTeC-style desktop telemetry analysis tool built in Python 
using real F1 race data from the 2024 season.

Built by an MSc Motorsport Engineering graduate to replicate 
core MoTeC i2 Pro functionality using open-source tools.

What It Does : 
- Pulls real F1 race telemetry via FastF1 API
- Derives wheel torque from first principles 
  (wheel inertia + longitudinal acceleration)
- 7-channel synchronised plot view:
  Speed · Longitudinal Acceleration · Wheel Torque · 
  Throttle · RPM · ΔThrottle · ΔWheel Torque
- Lap A vs Lap B overlay comparison
- Interactive cursor with live channel readout 
  at any track position

Tools & Libraries:
Tool(Purpose)
FastF1 (F1 telemetry data source )
PyQt6 (Desktop GUI framework)
pyqtgraph (Real-time plot rendering)
pandas (Data manipulation)
NumPy (Numerical computation) 

Circuits & Drivers Supported         
Monza (Italian GP), Spa (Belgian GP) — 2024 season
VER (Max Verstappen), NOR (Lando Norris) 

How to Run
1. Clone the repository
2. Install dependencies:
   pip install -r requirements.txt
3. Run the app:
   python telemetry_viewer.py


Author: Soham Sawant
MSc Motorsport Engineering — Oxford Brookes University

🌐 Portfolio: https://sohamsawant32.wixsite.com/s-performance
💼 LinkedIn: https://www.linkedin.com/in/soham-sawant/
