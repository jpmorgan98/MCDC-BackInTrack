import argparse, sys, time
import numpy as np

from numba import config

import type_, kernel, loop

from constant import *

# =============================================================================
# INPUT
# =============================================================================

# Model
SigmaC     = 0.25
SigmaS     = 0.5
SigmaF     = 0.25
nu         = 2.0
SigmaT     = SigmaC + SigmaS + SigmaF
X          = 3.0

# Technique
branchless_collision = True

# Parameters
N_particle = int(1E5)

# =============================================================================
# SETUP
# =============================================================================

# Mode, algorithm, and target
parser = argparse.ArgumentParser()
parser.add_argument('--mode', type=str, choices=['python', 'numba'], 
                    default='numba')
parser.add_argument('--alg', type=str, choices=['history', 'event'], 
                    default='history')
parser.add_argument('--target', type=str, choices=['cpu', 'gpu'],
                    default='cpu')
args, unargs = parser.parse_known_args()
alg = args.alg
target = args.target
mode = args.mode
if mode == 'python' and target == 'gpu':
    print('[ERROR] Python mode cannot run on GPU.')
    sys.exit()
if alg == 'history' and target == 'gpu':
    print('[ERROR] GPU run currently only supports event-based algorithm.')
    sys.exit()
if target == 'gpu' and not branchless_collision:
    print('[ERROR] GPU run currently has to run with branchless collision.')
    sys.exit()

# Pure python mode?
if mode == 'python':
    config.DISABLE_JIT = True
elif mode == 'numba':
    config.DISABLE_JIT = False

# Event stacks
if branchless_collision:
    # Remove scattering and fission
    N_stack = N_EVENT - 2
else:
    # Remove branchless_collision
    N_stack = N_EVENT - 1

# Make types, kernels, and loops
type_.make_type_global(N_particle, N_stack, alg)
kernel.make_kernels(alg, target)
loop.make_loops(alg, target)

# Allocate global variable container
mcdc = np.zeros(1, dtype=type_.global_)[0]

# ========================================
# Set global variables
# ========================================

# Model
mcdc['SigmaC'] = SigmaC
mcdc['SigmaS'] = SigmaS
mcdc['SigmaF'] = SigmaF
mcdc['nu']     = nu
mcdc['SigmaT'] = SigmaT
mcdc['X']      = X

# Technique
mcdc['branchless_collision'] = branchless_collision

# RNG
mcdc['rng_g']     = RNG_G
mcdc['rng_c']     = RNG_C
mcdc['rng_mod']   = RNG_MOD
mcdc['seed']      = RNG_SEED

# Mode-specifics
if alg == 'history':
    mcdc['history_based'] = True
    mcdc['N_history']     = N_particle
    mcdc['N_particle']    = 1
else:
    mcdc['history_based'] = False
    mcdc['N_history']     = 1
    mcdc['N_particle']    = N_particle

# Target-specifics
if target == 'gpu':
    mcdc['gpu']      = True
    mcdc['N_thread'] = 32
else:
    mcdc['gpu']      = False
    mcdc['N_thread'] = 1

# ========================================
# Event-based parameters and helpers
# ========================================

mcdc['N_stack']   = N_stack
mcdc['stack_idx'] = np.arange(N_EVENT)
mcdc['event_idx'] = np.arange(N_stack)

# To initiate stack-driven algorithm
mcdc['stack_'][EVENT_SOURCE]['size'] = mcdc['N_particle']
mcdc['stack_'][EVENT_NONE]['size']   = \
             mcdc['stack_'][EVENT_NONE]['content'].shape[0] - mcdc['N_particle']

# Strides
mcdc['history_stride']                           = RNG_STRIDE
mcdc['event_stride'][EVENT_SOURCE]               = 2
mcdc['event_stride'][EVENT_MOVE]                 = 2
mcdc['event_stride'][EVENT_SCATTERING]           = 1
mcdc['event_stride'][EVENT_FISSION]              = 2
mcdc['event_stride'][EVENT_LEAKAGE]              = 0
mcdc['event_stride'][EVENT_BRANCHLESS_COLLISION] = 1

# Branchless collision edits
if mcdc['branchless_collision']:
    # Replace (scattering, fission) with (leakage, branchless collision)
    mcdc['stack_idx'][EVENT_LEAKAGE]              = EVENT_SCATTERING
    mcdc['stack_idx'][EVENT_BRANCHLESS_COLLISION] = EVENT_FISSION
    mcdc['event_idx'][EVENT_SCATTERING]           = EVENT_LEAKAGE
    mcdc['event_idx'][EVENT_FISSION]              = EVENT_BRANCHLESS_COLLISION

    # Reduce move stride
    mcdc['event_stride'][EVENT_MOVE] = 1

# ========================================

# Make and set GPU host controller
hostco               = type_.get_hostco(N_stack)
hostco['N_thread']   = mcdc['N_thread']
hostco['stack_size'] = mcdc['stack_']['size']
hostco['event_idx']  = mcdc['event_idx']

# =============================================================================
# RUN
# =============================================================================

start = time.perf_counter()
loop.simulation(mcdc, hostco)
end = time.perf_counter()
print(mode, alg, target, mcdc['tally']/N_particle, end-start)
