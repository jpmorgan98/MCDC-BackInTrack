import math
import numpy as np

import numba
from numba import cuda, njit

from constant import *

import type_, adapter

# =============================================================================
# Events
# =============================================================================

leakeag_try = np.array([0,0], dtype=np.float32)
leakeag_tryd = cuda.to_device(leakeag_try)


def source(P, mcdc):
    P['x']     = -mcdc['X'] + 2.0*mcdc['X']*rng(P, mcdc)
    P['ux']    = -1.0 + 2.0*rng(P, mcdc)
    P['w']     = 1.0
    P['alive'] = True

    P['event'] = EVENT_MOVE

def move(P, mcdc):
    SigmaT = mcdc['SigmaT']
    SigmaC = mcdc['SigmaC']
    SigmaS = mcdc['SigmaS']
    X      = mcdc['X']

    # Sample collision distance
    distance  = -math.log(rng(P, mcdc))/SigmaT
    P['x']   += P['ux']*distance

    # Now, determine event

    # Leakage?
    if math.fabs(P['x']) > X:
        P['event'] = EVENT_LEAKAGE

    # Collision
    else:
        if mcdc['branchless_collision']:
            P['event'] = EVENT_BRANCHLESS_COLLISION
        else:
            xi = rng(P, mcdc)*SigmaT
            tot = SigmaC
            if tot > xi:
                terminate_particle(P)
                return
            else:
                tot += SigmaS
                if tot > xi:
                    P['event'] = EVENT_SCATTERING
                else:
                    P['event'] = EVENT_FISSION


def branchless_collision(P, mcdc):
    #print('in bc')
    SigmaT = mcdc['SigmaT']
    SigmaS = mcdc['SigmaS']
    SigmaF = mcdc['SigmaF']
    nu     = mcdc['nu']

    P['ux']  = -1.0 + 2.0*rng(P, mcdc)
    P['w']  *= (SigmaS + nu*SigmaF)/SigmaT

    P['event'] = EVENT_MOVE

def scattering(P, mcdc):
    P['ux'] = -1.0 + 2.0*rng(P, mcdc)
    
    P['event'] = EVENT_MOVE


def async_fission(P, mcdc):
    #print('in fission')
    nu = mcdc['nu']

    # Sample number of fission neutrons
    n = math.floor(nu + rng(P, mcdc))
    return n


def fission(P, mcdc):
    #print('in fission')
    nu = mcdc['nu']

    # Sample number of fission neutrons
    n = math.floor(nu + rng(P, mcdc))

    # Sample fission neutrons
    for i in range(n):
        P_new       = np.zeros(1, dtype=type_.particle_rec)[0]
        P_new['x']  = P['x']
        P_new['ux'] = -1.0 + 2.0*rng(P, mcdc)
        P_new['w']  = P['w']

        # Push to bank and update stack (for event-based)
        if mcdc['history_based']:
            idx = mcdc['bank']['size']
            mcdc['bank']['content'][idx] = P_new
            mcdc['bank']['size'] += 1
        else: # Event based
            # Get the index of the next idle particle in the bank
            mcdc['stack_'][EVENT_NONE]['size'] -= 1
            idx      = mcdc['stack_'][EVENT_NONE]['size']
            idx_bank = mcdc['stack_'][EVENT_NONE]['content'][idx]

            # Push the new particle
            mcdc['bank']['content'][idx_bank] = P_new

            # Mark the new particle in the bank in the next event stack
            idx = mcdc['stack_'][EVENT_MOVE]['size']
            mcdc['stack_'][EVENT_MOVE]['content'][idx]  = idx_bank
            mcdc['stack_'][EVENT_MOVE]['size']         += 1


    terminate_particle(P)

def leakage(P, mcdc): 
    #print('in leak')
    if P['ux'] > 0.0:
        atomic_add(mcdc['tally'], 1, 1)
        atomic_add(mcdc['tally'], 1, 2)
    else:
        atomic_add(mcdc['tally'], 1, 0)
        atomic_add(mcdc['tally'], 1, 2)
    
    terminate_particle(P)



# =============================================================================
# RNG
# =============================================================================

def rng(P, mcdc):
    seed     = int(P['seed'])
    g        = int(mcdc['rng_g'])
    c        = int(mcdc['rng_c'])
    mod      = int(mcdc['rng_mod'])
    mod_mask = int(mod - 1)

    mod_mask = int(mod - 1)

    P['seed'] = (g*seed + c) & mod_mask
    return P['seed']/mod

def rng_skip_ahead(n, P, mcdc):
    n        = int(n)
    seed     = int(P['seed'])
    g        = int(mcdc['rng_g'])
    c        = int(mcdc['rng_c'])
    mod      = int(mcdc['rng_mod'])
    mod_mask = int(mod - 1)
    g_new    = 1
    c_new    = 0
    
    n = n & mod_mask
    while n > 0:
        if n & 1:
            g_new = g_new*g       & mod_mask
            c_new = (c_new*g + c) & mod_mask

        c = (g+1)*c & mod_mask
        g = g*g     & mod_mask
        n >>= 1

    P['seed'] = (g_new*seed + c_new) & mod_mask
    #sync()

# =============================================================================
# Utilities
# =============================================================================

def record_particle(P):
    P_rec = create(type_.particle_rec)
    P_rec['x']  = P['x']
    P_rec['ux'] = P['ux']
    P_rec['w']  = P['w']
    #sync()
    return P_rec

def read_particle(P_rec):
    P = create(type_.particle)
    P['x']     = P_rec['x']
    P['ux']    = P_rec['ux']
    P['w']     = P_rec['w']
    P['alive'] = True
    #sync()
    return P

def terminate_particle(P):
    P['alive'] = False
    P['w']     = 0.0
    P['event'] = EVENT_NONE
    #sync()

# ==================================
# Utilities: hardware-specific
# ==================================

#def GPU_thread_id():
#    cuda.threadIdx

get_idx = None
def CPU_get_idx():
    return 0, 1
def GPU_get_idx():
    return cuda.grid(1), cuda.gridsize(1)

create = None
def CPU_create(dtype):
    return np.zeros(1, dtype=dtype)[0]
def GPU_create(dtype):
    return cuda.local.array(1, dtype=dtype)[0]

exscan = None
def CPU_exscan(a_in, a_out, N):
    for i in range(N-1):
        a_out[i+1,:] = a_out[i,:] + a_in[i,:]
# TODO!!!!!!!
# perform exclusive scan 
def GPU_exscan(a_in, a_out, N):
    for i in range(N-1):
        for j in range(a_in.shape[1]):
            a_out[i+1,j] = a_out[i,j] + a_in[i,j]

atomic_add = None
def GPU_atomic_add(vec, ammount, index):
    cuda.atomic.add(vec, index, ammount)

def CPU_atomic_add(vec, ammount, index):
    vec[index] += ammount

sync = None
def GPU_sync():
        cuda.syncthreads()

#@cuda.reduce
#def GPU_reduction(mcdc, flux):
#    cuda.ds

# ==================================
# Utilities: event-based
# ==================================

def initialize_stack(mcdc, hostco):
    N_particle = mcdc['stack_'][EVENT_SOURCE]['size']
    start, stride = get_idx()
    for i in range(start, N_particle, stride):
        mcdc['stack_'][EVENT_SOURCE]['content'][i] = i
    
    N = mcdc['stack_'][EVENT_NONE]['size']
    start, stride = get_idx()
    for i in range(start, N, stride):
        mcdc['stack_'][EVENT_NONE]['content'][i] = N_particle + i

# =============================================================================
# Factory
# =============================================================================

def make_kernels(alg, target):
    # =========================================================================
    # Functions
    # =========================================================================

    global fission
    if alg == 'async':
        target = 'gpu_device'
        fission = async_fission

    # RNG
    global rng, rng_skip_ahead
    rng            = adapter.compiler(rng, target)
    rng_skip_ahead = adapter.compiler(rng_skip_ahead, target)
    
    # ========================================
    # Utilities
    # ========================================

    global read_particle, record_particle, terminate_particle, get_idx, create,\
           exscan, atomic_add

    read_particle   = adapter.compiler(read_particle, target)
    record_particle = adapter.compiler(record_particle, target)
    terminate_particle = adapter.compiler(terminate_particle, target)
    if target == 'cpu':
        get_idx = adapter.compiler(CPU_get_idx, target)
        create  = adapter.compiler(CPU_create, target)
        exscan  = adapter.compiler(CPU_exscan, target)
        atomic_add = adapter.compiler(CPU_atomic_add, target)
    else:
        #! added gpu_device in place of target
        get_idx    = adapter.compiler(GPU_get_idx, target)
        create     = adapter.compiler(GPU_create, target)
        exscan     = adapter.compiler(GPU_exscan, target)
        atomic_add = adapter.compiler(GPU_atomic_add, target)
        sync       = adapter.compiler(GPU_sync, target)

    global initialize_stack

    initialize_stack = adapter.compiler(initialize_stack, target)
    
    # =========================================================================
    # Events
    # =========================================================================

    global source, move, leakage, scattering, branchless_collision
    
    source                  = adapter.event(source, alg, target, EVENT_SOURCE)
    move                    = adapter.event(move, alg, target, EVENT_MOVE) #, branching=True)
    leakage                 = adapter.event(leakage, alg, target, EVENT_LEAKAGE)
    scattering              = adapter.event(scattering, alg, target, EVENT_SCATTERING)
    fission                 = adapter.event(fission, alg, target, EVENT_FISSION, naive=True)
    branchless_collision    = adapter.event(branchless_collision, alg, target, EVENT_BRANCHLESS_COLLISION)

    print(source)
    





