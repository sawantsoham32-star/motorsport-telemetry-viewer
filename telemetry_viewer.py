import sys
import os
import numpy as np
import pandas as pd
import fastf1

from PyQt6 import QtWidgets, QtCore
import pyqtgraph as pg

# =========================================================
# FastF1 cache
# =========================================================
CACHE_DIR = "fastf1_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

# =========================================================
# Constants (APPROVED – DO NOT CHANGE)
# =========================================================
YEAR = 2024
VEHICLE_MASS = 800.0
WHEEL_RADIUS = 0.33
WHEEL_INERTIA = 1.2

DRIVERS = {"VER": "Max Verstappen", "NOR": "Lando Norris"}
TRACKS = {"Monza": "Italian Grand Prix", "Spa": "Belgian Grand Prix"}

# =========================================================
# Telemetry Loader (cached)
# =========================================================
telemetry_cache = {}

def load_lap(driver, track, lap_no):
    key = (driver, track, lap_no)
    if key in telemetry_cache:
        return telemetry_cache[key]

    session = fastf1.get_session(YEAR, TRACKS[track], "R")
    session.load()

    lap = session.laps.pick_driver(driver).pick_lap(lap_no)
    tel = lap.get_car_data().add_distance()

    df = tel[["Distance", "Speed", "Throttle", "RPM", "Brake"]].copy()
    df["Speed_mps"] = df["Speed"] / 3.6
    df["Ax"] = np.gradient(df["Speed_mps"], df["Distance"])

    df["Wheel_Omega"] = df["Speed_mps"] / WHEEL_RADIUS
    df["Wheel_Alpha"] = np.gradient(df["Wheel_Omega"], df["Distance"])

    # EXACT SAME wheel torque logic
    df["Wheel_Torque"] = (
        WHEEL_INERTIA * df["Wheel_Alpha"]
        + VEHICLE_MASS * df["Ax"] * WHEEL_RADIUS
    )

    df["Delta_Throttle"] = df["Throttle"].diff()
    df["Delta_Wheel_Torque"] = df["Wheel_Torque"].diff()

    telemetry_cache[key] = df
    return df

# =========================================================
# Main Viewer
# =========================================================
class TelemetryViewer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Motorsport Telemetry Viewer (MoTeC-style)")
        self.resize(1700, 950)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)

        # ---------------- Control Panel ----------------
        controls = QtWidgets.QHBoxLayout()

        self.driver_box = QtWidgets.QComboBox()
        self.driver_box.addItems(DRIVERS.keys())

        self.track_box = QtWidgets.QComboBox()
        self.track_box.addItems(TRACKS.keys())

        self.lapA = QtWidgets.QSpinBox()
        self.lapA.setRange(1, 80)
        self.lapA.setValue(2)

        self.lapB = QtWidgets.QSpinBox()
        self.lapB.setRange(1, 80)
        self.lapB.setValue(3)

        self.load_btn = QtWidgets.QPushButton("Load Telemetry")
        self.load_btn.clicked.connect(self.load_data)

        for label, widget in [
            ("Driver", self.driver_box),
            ("Track", self.track_box),
            ("Lap A", self.lapA),
            ("Lap B", self.lapB),
        ]:
            controls.addWidget(QtWidgets.QLabel(label))
            controls.addWidget(widget)

        controls.addStretch()
        controls.addWidget(self.load_btn)
        main_layout.addLayout(controls)

        # ---------------- Content ----------------
        content = QtWidgets.QHBoxLayout()
        main_layout.addLayout(content)

        # ----------- Plots ----------------
        self.plot_widget = pg.GraphicsLayoutWidget()
        content.addWidget(self.plot_widget, 4)

        self.channels = [
            ("Speed [km/h]", "Speed"),
            ("Longitudinal Accel [m/s²]", "Ax"),
            ("Wheel Torque [Nm]", "Wheel_Torque"),
            ("Throttle [%]", "Throttle"),
            ("RPM", "RPM"),
            ("Δ Throttle", "Delta_Throttle"),
            ("Δ Wheel Torque", "Delta_Wheel_Torque"),
        ]

        self.plots = []
        self.cursor_lines = []
        self.data = {}

        for i, (title, _) in enumerate(self.channels):
            p = self.plot_widget.addPlot(row=i, col=0)
            p.setLabel("left", title)
            p.showGrid(x=True, y=True, alpha=0.3)
            if i < len(self.channels) - 1:
                p.hideAxis("bottom")
            self.plots.append(p)

        for p in self.plots[1:]:
            p.setXLink(self.plots[0])

        # ----------- Cursor Readout Panel --------------
        self.readout = QtWidgets.QTextEdit()
        self.readout.setReadOnly(True)
        self.readout.setMinimumWidth(350)
        content.addWidget(self.readout, 1)

        # Mouse tracking
        self.proxy = pg.SignalProxy(
            self.plot_widget.scene().sigMouseMoved,
            rateLimit=60,
            slot=self.mouse_moved
        )

    # -------------------------------------------------
    def load_data(self):
        for p in self.plots:
            p.clear()
        self.cursor_lines.clear()
        self.data.clear()

        driver = self.driver_box.currentText()
        track = self.track_box.currentText()

        laps = {
            "Lap A": self.lapA.value(),
            "Lap B": self.lapB.value()
        }

        colors = {"Lap A": "r", "Lap B": "g"}

        for label, lap in laps.items():
            df = load_lap(driver, track, lap)
            self.data[label] = df

            for i, (_, col) in enumerate(self.channels):
                self.plots[i].plot(
                    df["Distance"],
                    df[col],
                    pen=pg.mkPen(colors[label], width=1),
                    name=label
                )

        # Cursor lines
        for p in self.plots:
            v = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("y"))
            p.addItem(v)
            self.cursor_lines.append(v)

    # -------------------------------------------------
    def mouse_moved(self, evt):
        pos = evt[0]
        if not self.plots:
            return

        if self.plots[0].sceneBoundingRect().contains(pos):
            mouse_point = self.plots[0].vb.mapSceneToView(pos)
            x = mouse_point.x()

            # Move cursor
            for v in self.cursor_lines:
                v.setPos(x)

            # Update readout
            self.update_readout(x)

    # -------------------------------------------------
    def update_readout(self, x):
        lines = [f"Distance: {x:.1f} m\n"]

        for name, col in self.channels:
            line = f"{name:<25}"
            for lap_label, df in self.data.items():
                y = np.interp(x, df["Distance"], df[col])
                line += f"{lap_label}: {y:8.2f}   "
            lines.append(line)

        self.readout.setText("\n".join(lines))


# =========================================================
# Run
# =========================================================
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    viewer = TelemetryViewer()
    viewer.show()
    sys.exit(app.exec())
