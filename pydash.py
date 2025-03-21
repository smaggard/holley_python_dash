import ttkbootstrap as ttk
import threading
import struct
import can
import logging
import sys
from systemd.journal import JournalHandler
from ttkbootstrap.constants import *
from time import sleep

# Setup logging
log = logging.getLogger('dashboard')
log.addHandler(JournalHandler())
log.setLevel(logging.INFO)

# Create a shared dictionary for the gauge to CAN ID association
global can_ids
can_ids = {
        0x1E005104: {"name": "tachometer", "round_pos": 0},
        0x1E371104: {"name": "speedometer", "round_pos": 0},
        0x1E085104: {"name": "voltmeter", "round_pos": 1},
        0x1E089104: {"name": "oilometer", "round_pos": 1},
        0x1E07D104: {"name": "coolant_temp", "round_pos": 1},
        0x1E679104: {"name": "fuelometer", "round_pos": 0},
        0x1E019104: {"name": "afr_left", "round_pos": 2},
        0x1E01D104: {"name": "afr_right", "round_pos": 2},
        0x1E021104: {"name": "afr_avg", "round_pos": 2},
        0x1E385104: {"name": "trans_temp", "round_pos": 1},
        0x1E4D1104: {"name": "outside_temp", "round_pos": 0},
        0x1E4D5104: {"name": "outside_hum", "round_pos": 1},
        0x1E4B9104: {"name": "ps_temp", "round_pos": 1},
        0x1E4A9104: {"name": "oil_temp", "round_pos": 1},
        0x1E4ED104: {"name": "drv_frnt_tire", "round_pos": 1},
        0x1E4F5104: {"name": "drv_rear_tire", "round_pos": 1},
        0x1E4F1104: {"name": "pass_frnt_tire", "round_pos": 1},
        0x1E4F9104: {"name": "pass_rear_tire", "round_pos": 1},
    }

# Create and return a Meter object.
def create_gauge(size: int, total: int, subtext: str) -> ttk.Meter:
    return ttk.Meter(
        metersize=size,
        padding=0,
        amountused=25,
        amounttotal=total,
        metertype="semi",
        subtext=subtext,
        subtextfont='-size 8',
        interactive=False,
        bootstyle=("light"),
        stripethickness=3,
    )

# Convert Hex to Floating point.
def hex_to_float(f: str) -> float:
    return struct.unpack('!f',bytes.fromhex(f))[0]

# Can listener thread that updates gauges as they are seen.
def can_listener() -> None:
    try:
        log.info("Starting Can Interface")
        # Set the initial value to 0 to prevent a key error
        for key in can_ids.keys():
            can_ids[key]['value'] = 0
        # Open CAN interface and continuously listen
        with can.interface.Bus(channel='can0', interface='socketcan') as Bus:
            for msg in Bus:
                # If the CAN ID is in the known list, process it.
                if msg.arbitration_id in can_ids.keys():
                    # Grab the first 4 bytes.
                    round_pos = can_ids[msg.arbitration_id]['round_pos']
                    raw_bytes = str(msg.data.hex())[:8]
                    # Convert hex to floating point
                    value = hex_to_float(raw_bytes)
                    # Update gauge with new value if its new.
                    if can_ids[msg.arbitration_id]['value'] != round(value, round_pos):
                        # Update Dictionary Value
                        can_ids[msg.arbitration_id]['value'] = round(value, round_pos)
                        # Update Gauge.
                        can_ids[msg.arbitration_id]['gauge'].configure(amountused = round(value, round_pos))
    except Exception as e:
        log.error(e)

def main() -> None:
    app = ttk.Window(themename="cyborg", size=(1920, 480), title="1972 Camaro Dash")
    # Configure columns and rows.
    for i in range(8):
        app.columnconfigure(i, weight=1)

    for i in range(3):
        app.rowconfigure(i, weight=1)

    # Create all the gauges and update them in the global dictionary
    afr_left = create_gauge(140, 20, "AFR Left")
    can_ids[0x1E019104]['gauge'] = afr_left
    afr_right = create_gauge(140, 20, "AFR Right")
    can_ids[0x1E01D104]['gauge'] = afr_right
    afr_avg = create_gauge(140, 20, "AFR Average")
    can_ids[0x1E021104]['gauge'] = afr_avg
    ps_temp = create_gauge(140, 260, "Power Steer °F")
    can_ids[0x1E4B9104]['gauge'] = ps_temp
    outside_temp = create_gauge(140, 120, "Outside °F")
    can_ids[0x1E4D1104]['gauge'] = outside_temp
    outside_hum = create_gauge(140, 100, "Outside Hum %")
    can_ids[0x1E4D5104]['gauge'] = outside_hum
    speedometer = create_gauge(360, 160, "MPH")
    can_ids[0x1E371104]['gauge'] = speedometer
    voltmeter = create_gauge(140, 16, "Volts")
    can_ids[0x1E085104]['gauge'] = voltmeter
    oilometer = create_gauge(140, 120, "Oil PSI")
    can_ids[0x1E089104]['gauge'] = oilometer
    oiltemp = create_gauge(140, 300, "Oil Temp °F")
    can_ids[0x1E4A9104]['gauge'] = oiltemp
    coolant_temp = create_gauge(140, 260, "Engine Temp °F")
    can_ids[0x1E07D104]['gauge'] = coolant_temp
    trans_temp = create_gauge(140, 260, "Trans Temp °F")
    can_ids[0x1E385104]['gauge'] = trans_temp
    fuelometer = create_gauge(140, 100, "FUEL %")
    can_ids[0x1E679104]['gauge'] = fuelometer
    tachometer = create_gauge(360, 8000, "RPM")
    can_ids[0x1E005104]['gauge'] = tachometer
    drv_frnt_tire = create_gauge(120, 50, "Driver Front")
    can_ids[0x1E4ED104]['gauge'] = drv_frnt_tire
    drv_rear_tire = create_gauge(120, 50, "Driver Rear")
    can_ids[0x1E4F5104]['gauge'] = drv_rear_tire
    pass_frnt_tire = create_gauge(120, 50, "Pass Front")
    can_ids[0x1E4F1104]['gauge'] = pass_frnt_tire
    pass_rear_tire = create_gauge(120, 50, "Pass Rear")
    can_ids[0x1E4F9104]['gauge'] = pass_rear_tire

    # Create the Grid.
    afr_left.grid(column=0, row=0, sticky=NSEW)
    afr_right.grid(column=0, row=1, sticky=NSEW)
    afr_avg.grid(column=0, row=2, sticky=NSEW)
    voltmeter.grid(column=1, row=0, sticky=NSEW)
    oilometer.grid(column=1, row=1, sticky=NSEW)
    oiltemp.grid(column=1, row=2, sticky=NSEW)
    speedometer.grid(column=2, row=0, sticky=NSEW, rowspan=2, columnspan=2)
    drv_frnt_tire.grid(column=2, row=2, sticky=NSEW, rowspan=1)
    drv_rear_tire.grid(column=3, row=2, sticky=NSEW, rowspan=1)
    tachometer.grid(column=4, row=0, sticky=NSEW, rowspan=2, columnspan=2)
    pass_frnt_tire.grid(column=4, row=2, sticky=NSEW, rowspan=1)
    pass_rear_tire.grid(column=5, row=2, sticky=NSEW, rowspan=1)
    fuelometer.grid(column=6, row=0, sticky=NSEW)
    coolant_temp.grid(column=6, row=1, sticky=NSEW)
    trans_temp.grid(column=6, row=2, sticky=NSEW)
    ps_temp.grid(column=7, row=0, sticky=NSEW)
    outside_temp.grid(column=7, row=1, sticky=NSEW)
    outside_hum.grid(column=7, row=2, sticky=NSEW)

    # Start loop.
    app.mainloop()

if __name__ == "__main__":
    try:
        can_thread = threading.Thread(target=can_listener)
        gui_thread = threading.Thread(target=main)
        gui_thread.start()
        sleep(.5)
        can_thread.start()
        gui_thread.join()
        can_thread.join()
    except KeyboardInterrupt as e:
        sys.exit(1)
