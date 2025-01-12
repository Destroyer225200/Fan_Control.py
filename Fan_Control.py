from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QFormLayout, QSlider, QDial, QHBoxLayout, QTableWidget, QTableWidgetItem, QSplitter, QScrollArea
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette, QIcon
import numpy as np
import pandas as pd
import random

class FanControl(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Fan Control Application")
        self.setGeometry(100, 100, 1200, 800)  # Set window size for fullscreen optimization

        # Create main layout as a horizontal splitter for left and right sections
        main_splitter = QSplitter(Qt.Horizontal)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(main_splitter)

        # Scroll area for left layout to manage resizing
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        left_widget = QWidget()
        scroll_area.setWidget(left_widget)

        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)

        self.form_layout = QFormLayout()
        left_layout.addLayout(self.form_layout)

        self.air_intake_label = QLabel("Air Intake Control:")
        self.form_layout.addRow(self.air_intake_label)

        self.trape = []
        trap_names = ["Trap 1 - Front", "Trap 2 - Back", "Trap 3 - Auto Ventilation", "Trap 4 Natural air"]
        for i, name in enumerate(trap_names):
            trap_label = QLabel(f"{name}:")
            trap_slider = QSlider(Qt.Horizontal)
            trap_slider.setMinimum(0)
            trap_slider.setMaximum(4)
            trap_slider.setValue(0)
            trap_slider.setTickInterval(1)
            trap_slider.setTickPosition(QSlider.TicksBelow)

            # Create labels for tick positions
            tick_labels = QHBoxLayout()
            for percentage in ["0%", "25%", "50%", "75%", "100%"]:
                label = QLabel(percentage)
                tick_labels.addWidget(label)

            # Create buttons and layout for Open/Close
            button_layout = QHBoxLayout()
            trap_open_button = QPushButton("Open +25%")
            trap_open_button.setStyleSheet("background-color: green; color: white;")
            trap_close_button = QPushButton("Close")
            trap_close_button.setStyleSheet("background-color: red; color: white;")
            trap_color_label = QLabel()
            trap_color_label.setAutoFillBackground(True)
            trap_color_label.setFixedSize(50, 20)

            button_layout.addWidget(trap_open_button)
            button_layout.addWidget(trap_close_button)
            button_layout.addWidget(trap_color_label)

            self.trape.append({
                'slider': trap_slider,
                'open_button': trap_open_button,
                'close_button': trap_close_button,
                'color_label': trap_color_label,
                'open_count': 0
            })

            trap_slider.valueChanged.connect(lambda value, idx=i: self.update_trap_color(idx, value))
            trap_open_button.clicked.connect(lambda _, idx=i: self.increment_trap_open(idx))
            trap_close_button.clicked.connect(lambda _, idx=i: self.reset_trap(idx))

            self.update_trap_color(i, 0)  # Initialize color

            h_layout = QVBoxLayout()
            slider_and_ticks = QVBoxLayout()
            slider_and_ticks.addWidget(trap_slider)
            slider_and_ticks.addLayout(tick_labels)

            h_layout.addLayout(slider_and_ticks)
            h_layout.addLayout(button_layout)

            self.form_layout.addRow(trap_label)
            self.form_layout.addRow(h_layout)

        # Ventilators and heat pumps for Trap 1 and Trap 2
        for i in range(2):
            vent_label = QLabel(f"Ventilator for {trap_names[i]}:")
            vent_on_button = QPushButton("Turn On")
            vent_on_button.setStyleSheet("background-color: green; color: white;")
            vent_off_button = QPushButton("Turn Off")

            pump_label = QLabel(f"Heat Pump for {trap_names[i]}:")
            pump_temp_label = QLabel("Temperature (°C): 0")
            pump_slider = QSlider(Qt.Horizontal)
            pump_slider.setMinimum(0)
            pump_slider.setMaximum(30)
            pump_slider.setValue(0)

            # Increment and Decrement Buttons
            increment_button = QPushButton("+10°C")
            decrement_button = QPushButton("-10°C")
            increment_button.setStyleSheet("background-color: orange; color: black;")
            decrement_button.setStyleSheet("background-color: blue; color: white;")
            increment_button.clicked.connect(lambda _, idx=i: self.increment_temperature(idx, 10))
            decrement_button.clicked.connect(lambda _, idx=i: self.increment_temperature(idx, -10))

            pump_slider.valueChanged.connect(lambda value, idx=i: self.update_pump_temp(idx, value))

            self.form_layout.addRow(vent_label)
            self.form_layout.addRow(vent_on_button, vent_off_button)
            self.form_layout.addRow(pump_label)
            self.form_layout.addRow(pump_temp_label, pump_slider)

            button_row = QHBoxLayout()
            button_row.addWidget(increment_button)
            button_row.addWidget(decrement_button)
            self.form_layout.addRow(button_row)

            vent_on_button.clicked.connect(lambda _, idx=i: self.turn_on_vent(idx))
            vent_off_button.clicked.connect(lambda _, idx=i: self.turn_off_vent(idx))

            self.trape[i].update({
                'vent_on_button': vent_on_button,
                'vent_off_button': vent_off_button,
                'pump_temp_label': pump_temp_label,
                'pump_slider': pump_slider
            })

        # Heat pump and fan speed control integration
        self.temp_control = Temp_Control()
        left_layout.addLayout(self.temp_control.form_layout)

        # Temperature control for air input
        self.air_temp_label = QLabel("Air Input Temperature (°C): 0")
        self.air_temp_slider = QSlider(Qt.Horizontal)
        self.air_temp_slider.setMinimum(0)
        self.air_temp_slider.setMaximum(120)
        self.air_temp_slider.setValue(0)
        self.air_temp_slider.valueChanged.connect(self.update_air_temp)
        self.form_layout.addRow(self.air_temp_label, self.air_temp_slider)

        # Add scrollable left widget to splitter
        main_splitter.addWidget(scroll_area)

        # Right layout for the temperature tables
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)

        # Temperature table for hubs
        self.hub_temperature_table = QTableWidget()
        self.hub_temperature_table.setRowCount(4)  # Four hubs
        self.hub_temperature_table.setColumnCount(2)  # Hub and Temperature
        self.hub_temperature_table.setHorizontalHeaderLabels(["Hub", "Temperature (°C)"])
        for i in range(4):
            self.hub_temperature_table.setItem(i, 0, QTableWidgetItem(f"Hub {i + 1}"))
            self.hub_temperature_table.setItem(i, 1, QTableWidgetItem("0"))

        right_layout.addWidget(self.hub_temperature_table)

        # Temperature table for soil sensors
        self.soil_temperature_table = QTableWidget()
        self.soil_temperature_table.setRowCount(10)  # Nine sensors + one row for average
        self.soil_temperature_table.setColumnCount(2)  # Sensor and Temperature
        self.soil_temperature_table.setHorizontalHeaderLabels(["Sensor", "Temperature (°C)"])
        for i in range(9):
            self.soil_temperature_table.setItem(i, 0, QTableWidgetItem(f"Sensor {i + 1}"))
            self.soil_temperature_table.setItem(i, 1, QTableWidgetItem("0"))
        self.soil_temperature_table.setItem(9, 0, QTableWidgetItem("Average"))
        self.soil_temperature_table.setItem(9, 1, QTableWidgetItem("0"))

        right_layout.addWidget(self.soil_temperature_table)

        # Add right widget to splitter
        main_splitter.addWidget(right_widget)
        main_splitter.setStretchFactor(0, 2)  # Left section takes 2/3
        main_splitter.setStretchFactor(1, 1)  # Right section takes 1/3

    def update_trap_color(self, idx, value):
        color_label = self.trape[idx]['color_label']
        palette = color_label.palette()

        if value == 0:
            color = QColor("white")
        elif value == 1:
            color = QColor(200, 220, 255)  #  blue - mai multe nuante de albastru progresiv
        elif value == 2:
            color = QColor(150, 190, 255)
        elif value == 3:
            color = QColor(100, 160, 255)
        elif value == 4:
            color = QColor(50, 130, 255)

        palette.setColor(QPalette.Window, color)
        color_label.setPalette(palette)

    def increment_trap_open(self, idx):
        trap = self.trape[idx]
        trap['open_count'] = (trap['open_count'] + 1) % 5  # Cycle through 0-4
        value = trap['open_count']
        trap['slider'].setValue(value)
        trap['open_button'].setText(f"Open +{value * 25}%")
        print(f"{['Trap 1 - Front', 'Trap 2 - Back', 'Trap 3 - Auto Ventilation', 'Trap 4 - Natural Air'][idx]} set to {value * 25}%")

    def reset_trap(self, idx):
        trap = self.trape[idx]
        trap['slider'].setValue(0)
        trap['open_count'] = 0
        trap['open_button'].setText("Open +25%")
        print(f"{['Trap 1 - Front', 'Trap 2 - Back', 'Trap 3 - Auto Ventilation', 'Trap 4 - Natural Air'][idx]} reset to 0%")

    def turn_on_vent(self, idx):
        print(f"Ventilator for {['Trap 1 - Front', 'Trap 2 - Back'][idx]} is ON")

    def turn_off_vent(self, idx):
        print(f"Ventilator for {['Trap 1 - Front', 'Trap 2 - Back'][idx]} is OFF")

    def update_pump_temp(self, idx, value):
        self.trape[idx]['pump_temp_label'].setText(f"Temperature (°C): {value}")
        power_consumption = value * 1.5  # Example formula for power consumption
        efficiency = 100 - (value * 2)  # Example formula for efficiency
        print(f"Heat Pump for {['Trap 1 - Front', 'Trap 2 - Back'][idx]} - Temperature: {value}°C, Power: {power_consumption}W, Efficiency: {efficiency}%")

    def increment_temperature(self, idx, increment):
        current_value = self.trape[idx]['pump_slider'].value()
        new_value = max(0, min(30, current_value + increment))  # Clamp between 0 and 30
        self.trape[idx]['pump_slider'].setValue(new_value)

    def update_air_temp(self, value):
        self.air_temp_label.setText(f"Air Input Temperature (°C): {value}")
        print(f"Air input temperature set to {value}°C")

        # Update hub temperature table proportionally
        base_temperature = value - random.randint(5, 10)  # Slightly lower base temperature
        for i in range(4):
            adjusted_temp = base_temperature + random.uniform(0, 2)  # Small variation
            self.hub_temperature_table.setItem(i, 1, QTableWidgetItem(f"{adjusted_temp:.1f}"))

        # Update soil temperature table and calculate average
        soil_temperatures = [base_temperature - random.uniform(1, 3) + random.uniform(0, 2) for _ in range(9)]
        for i, temp in enumerate(soil_temperatures):
            self.soil_temperature_table.setItem(i, 1, QTableWidgetItem(f"{temp:.1f}"))

        average_temp = np.mean(soil_temperatures)
        self.soil_temperature_table.setItem(9, 1, QTableWidgetItem(f"{average_temp:.1f}"))

class Temp_Control(QWidget):
    def __init__(self):
        super().__init__()  # Call the parent constructor
        self.layout = QVBoxLayout() # Create a layout

        self.form_layout = QFormLayout()

        # Heat pumps control
        self.heat_pump_label = QLabel("Heat Pump Power:")
        self.heat_pump_slider = QSlider(Qt.Horizontal)
        self.heat_pump_slider.setRange(0, 3)  # Only 4 steps: 0, 1, 2, 3
        self.heat_pump_slider.setTickPosition(QSlider.TicksBelow)
        self.heat_pump_slider.setTickInterval(1)
        self.form_layout.addRow(self.heat_pump_label, self.heat_pump_slider)

        # Add Increase and Decrease buttons
        self.increase_button = QPushButton("Increase")
        self.decrease_button = QPushButton("Decrease")
        self.increase_button.setStyleSheet("background-color: lightblue; color: black;")
        self.decrease_button.setStyleSheet("background-color: darkblue; color: white;")
        self.form_layout.addRow(self.increase_button, self.decrease_button)

        self.increase_button.clicked.connect(self.increase_heat_pump_power)
        self.decrease_button.clicked.connect(self.decrease_heat_pump_power)

        # Fans control
        self.fan_label = QLabel("Fan Speed: 0W")  # Default label
        self.fan_dial = QDial()
        self.fan_dial.setRange(0, 220)  # Range from 0 to 220W
        self.fan_dial.setNotchesVisible(True)
        self.fan_dial.setStyleSheet("background-color: lightgrey; border-radius: 10px;")
        self.fan_dial.valueChanged.connect(self.update_fan_speed_label)
        self.form_layout.addRow(self.fan_label, self.fan_dial)

        # Add mode-switch button
        self.mode_button = QPushButton("Switch Mode")
        self.form_layout.addRow(self.mode_button)
        self.mode_button.clicked.connect(self.switch_mode)
        self.modes = [0, 60, 120, 180, 220]  # Predefined modes
        self.current_mode_index = 0

        # Add Fan power display
        self.fan_power_label = QPushButton("Fan Power: 0W")
        self.fan_power_label.setStyleSheet("background-color: grey; color: white;")
        self.fan_power_label.setEnabled(False)
        self.form_layout.addRow(self.fan_power_label)

        self.fan_dial.valueChanged.connect(self.update_fan_power)

        # Air intakes control
        self.air_intake_label = QLabel("Air Intake Control:")
        self.open_air_intake_button = QPushButton("Open Air Intake")
        self.open_air_intake_button.setStyleSheet("background-color: green; color: white;")
        self.close_air_intake_button = QPushButton("Close Air Intake")
        self.form_layout.addRow(self.air_intake_label)
        self.form_layout.addRow(self.open_air_intake_button, self.close_air_intake_button)

        self.setLayout(self.layout)

        # Connect buttons to functions
        self.open_air_intake_button.clicked.connect(self.open_air_intake)
        self.close_air_intake_button.clicked.connect(self.close_air_intake)

    def open_air_intake(self):
        print("Opening air intake")

    def close_air_intake(self):
        print("Closing air intake")

    def increase_heat_pump_power(self):
        current_value = self.heat_pump_slider.value()
        if current_value < 3:
            self.heat_pump_slider.setValue(current_value + 1)
            print(f"Heat Pump Power increased to {current_value + 1}")

    def decrease_heat_pump_power(self):
        current_value = self.heat_pump_slider.value()
        if current_value > 0:
            self.heat_pump_slider.setValue(current_value - 1)
            print(f"Heat Pump Power decreased to {current_value - 1}")

    def update_fan_power(self, value):
        power = value  # Directly map dial value to power
        self.fan_power_label.setText(f"Fan Power: {power}W")

    def update_fan_speed_label(self, value):
        self.fan_label.setText(f"Fan Speed: {value}W")

    def switch_mode(self):
        self.current_mode_index = (self.current_mode_index + 1) % len(self.modes)
        mode_value = self.modes[self.current_mode_index]
        self.fan_dial.setValue(mode_value)
        print(f"Switched to mode with {mode_value}W")

if __name__ == "__main__":
    app = QApplication([])
    app.setWindowIcon(QIcon("Icon.png"))

    window = FanControl()
    window.show()
    app.exec_()

