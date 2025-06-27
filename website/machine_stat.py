class CPRMachineStatus:
    def __init__(self):
        self.electric_shocks = 0
        self.cpr_cycles = 0
        self.breathe = 0
        self.start_time = None

    def update_status(self, shocks=0, cpr_cycles=0, ventilations=0):
        self.electric_shocks += shocks
        self.cpr_cycles += cpr_cycles
        self.breathe += ventilations

    def set_start(self, start_time):
        self.start_time = start_time
