import argparse
import m5
from m5.objects import *


# ------------------------------------------------------------
# Command-line parameters
# ------------------------------------------------------------

parser = argparse.ArgumentParser()

parser.add_argument(
    "--cpu",
    choices=["timing", "o3"],
    default="timing",
    help="CPU model: timing or o3",
)

parser.add_argument("--l2-size", default="512KiB")
parser.add_argument("--l2-assoc", type=int, default=4)

parser.add_argument("--l3-size", default="1MiB")
parser.add_argument("--l3-assoc", type=int, default=8)

args = parser.parse_args()


# ------------------------------------------------------------
# System
# ------------------------------------------------------------

system = System()

system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()

system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MiB")]


# ------------------------------------------------------------
# CPU
# ------------------------------------------------------------

if args.cpu == "timing":
    system.cpu = RiscvTimingSimpleCPU()
else:
    system.cpu = RiscvO3CPU()


# ------------------------------------------------------------
# L1 Instruction Cache
# ------------------------------------------------------------

system.cpu.icache = Cache(
    size="16KiB",
    assoc=2,
    tag_latency=2,
    data_latency=2,
    response_latency=2,
    mshrs=4,
    tgts_per_mshr=20,
)


# ------------------------------------------------------------
# L1 Data Cache
# ------------------------------------------------------------

system.cpu.dcache = Cache(
    size="16KiB",
    assoc=2,
    tag_latency=2,
    data_latency=2,
    response_latency=2,
    mshrs=4,
    tgts_per_mshr=20,
)


# ------------------------------------------------------------
# CPU -> L1
# ------------------------------------------------------------

system.cpu.icache.cpu_side = system.cpu.icache_port
system.cpu.dcache.cpu_side = system.cpu.dcache_port


# ------------------------------------------------------------
# L2 bus
# ------------------------------------------------------------

system.l2bus = L2XBar()

system.cpu.icache.mem_side = system.l2bus.cpu_side_ports
system.cpu.dcache.mem_side = system.l2bus.cpu_side_ports


# ------------------------------------------------------------
# L2 Cache
# ------------------------------------------------------------

system.l2cache = Cache(
    size=args.l2_size,
    assoc=args.l2_assoc,
    tag_latency=10,
    data_latency=10,
    response_latency=10,
    mshrs=16,
    tgts_per_mshr=20,
)

system.l2cache.cpu_side = system.l2bus.mem_side_ports


# ------------------------------------------------------------
# L3 bus
# ------------------------------------------------------------

system.l3bus = L2XBar()

system.l2cache.mem_side = system.l3bus.cpu_side_ports


# ------------------------------------------------------------
# L3 Cache
# ------------------------------------------------------------

system.l3cache = Cache(
    size=args.l3_size,
    assoc=args.l3_assoc,
    tag_latency=20,
    data_latency=20,
    response_latency=20,
    mshrs=32,
    tgts_per_mshr=20,
)

system.l3cache.cpu_side = system.l3bus.mem_side_ports


# ------------------------------------------------------------
# Main memory bus
# ------------------------------------------------------------

system.membus = SystemXBar()

system.l3cache.mem_side = system.membus.cpu_side_ports

system.system_port = system.membus.cpu_side_ports


# ------------------------------------------------------------
# Interrupt controller
# ------------------------------------------------------------

system.cpu.createInterruptController()


# ------------------------------------------------------------
# Main memory
# ------------------------------------------------------------

system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports


# ------------------------------------------------------------
# qsort_large benchmark
# ------------------------------------------------------------

binary = (
    "/home/tewar/CA_Assignment1/work/"
    "mibench/automotive/qsort/qsort_large.elf"
)

input_file = (
    "/home/tewar/CA_Assignment1/work/"
    "mibench/automotive/qsort/input_large.dat"
)

system.workload = SEWorkload.init_compatible(binary)

process = Process()
process.cmd = [binary, input_file]

system.cpu.workload = process
system.cpu.createThreads()


# ------------------------------------------------------------
# Start simulation
# ------------------------------------------------------------

root = Root(full_system=False, system=system)

m5.instantiate()

print("==============================================")
print("Starting qsort_large simulation")
print(f"CPU : {args.cpu}")
print(f"L2  : {args.l2_size}, {args.l2_assoc}-way")
print(f"L3  : {args.l3_size}, {args.l3_assoc}-way")
print("==============================================")

exit_event = m5.simulate()

print(
    f"Exiting @ tick {m5.curTick()} "
    f"because {exit_event.getCause()}"
)