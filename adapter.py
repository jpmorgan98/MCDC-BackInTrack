
import numba
from numba import njit, cuda, jit

import type_, kernel

from constant import *

#event = None

@cuda.jit(device=True)
def syncthreads():
    numba.cuda.syncthreads()


# =============================================================================
# Loop adapters
# =============================================================================

def loop(func, target):
    if target == 'cpu':
        return jit(func)
    else:
        def wrap(mcdc, hostco):
            # Create device copies
            #d_mcdc = cuda.to_device(mcdc)
            func(mcdc, hostco)
            #d_mcdc.copy_to_host(mcdc)
        return wrap




# =============================================================================
# Kernel adapters
# =============================================================================

def event(func, alg, target, event, branching=False, naive=False):
    func = compiler(func, "gpu_device")

    if alg != 'event':
        return func

    # Event-based zone below

    wrap = None

    def wrap_streaming(mcdc, hostco):

        nonlocal func

        # Stack index of the current event
        stack = mcdc['stack_idx'][event]
        
        # Stack size
        N = mcdc['stack_'][stack]['size']
        start, stride = kernel.get_idx()
        for i in range(start, N, stride):
            # Get particle index from stack
            idx = mcdc['stack_'][stack]['content'][i]
            
            # "Pop" particle from bank
            P = kernel.read_particle(mcdc['bank']['content'][idx])

            # Set RNG seed
            P['seed'] = mcdc['seed']
            kernel.rng_skip_ahead(i*mcdc['event_stride'][event], P, mcdc)

            # Perform event
            func(P, mcdc)
           
            # Update particle in the bank
            mcdc['bank']['content'][idx] = kernel.record_particle(P)
               
            # Get stack index of the next event
            next_event = P['event']
            next_stack = mcdc['stack_idx'][next_event]

            # Update stack of the next event
            idx_offset = mcdc['stack_'][next_stack]['size']
            mcdc['stack_'][next_stack]['content'][idx_offset+i] = idx

            # If last particle 
            if i == N-1:
                # Update main seed
                mcdc['seed'] = P['seed']

                # Reset current event stack size
                mcdc['stack_'][stack]['size'] = 0
                hostco['stack_size'][stack]   = 0

                # Update next event stack size
                mcdc['stack_'][next_stack]['size'] += N
                hostco['stack_size'][next_stack]   += N

    def wrap_branching(mcdc, hostco):
        # Stack index of the current event
        stack = mcdc['stack_idx'][event]
        # print(stack)

        # Stack size
        N = mcdc['stack_'][stack]['size']
        start, stride = kernel.get_idx()
        for i in range(start, N, stride):
            #syncthreads()
            # Get particle index from stack
            idx = mcdc['stack_'][stack]['content'][i]

            # "Pop" particle from bank
            P = kernel.read_particle(mcdc['bank']['content'][idx])

            # Set RNG seed
            P['seed'] = mcdc['seed']
            kernel.rng_skip_ahead(i*mcdc['event_stride'][event], P, mcdc)

            # Perform event
            func(P, mcdc)
           
            # Update particle in the bank
            mcdc['bank']['content'][idx] = kernel.record_particle(P)

            # Get stack index of the next event
            next_event = P['event']
            next_stack = mcdc['stack_idx'][next_event]

            # Update secondaries parameter (for sync. later)
            mcdc['secondaries_stack'][i]                = next_stack
            mcdc['secondaries_counter'][i, next_stack] += 1
            
            # If last particle 
            if i == N-1:
                # Update main seed
                mcdc['seed'] = P['seed']

                # Reset current event stack size
                mcdc['stack_'][stack]['size'] = 0
                hostco['stack_size'][stack]   = 0

        # Launch exclusive scan algorithm [M. Harris 2007]
        #  to get secondaries global indices
        if (cuda.threadIdx.x == 0):
            kernel.exscan(mcdc['secondaries_counter'], mcdc['secondaries_idx'], N)
            stride = 1
            # Update all events stack based on the secondaries parameters
            for i in range(start, N, stride):
                # Get the stack and index
                next_stack = mcdc['secondaries_stack'][i]
                idx        = mcdc['secondaries_idx'][i, next_stack] + \
                            mcdc['stack_'][next_stack]['size']
                            
                mcdc['stack_'][next_stack]['content'][idx] = \
                        mcdc['stack_'][stack]['content'][i]

                # If last particle, update stack sizes
                if i == N-1:
                    for j in range(mcdc['N_stack']):
                        # Get secondaries size
                        secondary_size = mcdc['secondaries_idx'][N-1,j] + \
                                        mcdc['secondaries_counter'][N-1,j]

                        # Update stack sizes
                        mcdc['stack_'][j]['size'] += secondary_size
                        hostco['stack_size'][j]   += secondary_size
                
                # Reset secondaries parameters
                for j in range(mcdc['N_stack']):
                    mcdc['secondaries_counter'][i, j] = 0
                    mcdc['secondaries_idx'][i, j]     = 0
        #syncthreads()
    
    def wrap_naive(mcdc, hostco, event):
        # Stack index of the current event
        stack = mcdc['stack_idx'][event]

        # Stack size
        N = mcdc['stack_'][stack]['size']
        start, stride = kernel.get_idx()
        for i in range(start, N, stride):
            # Get particle index from stack
            idx = mcdc['stack_'][stack]['content'][i]

            # "Pop" particle from bank
            P = kernel.read_particle(mcdc['bank']['content'][idx])

            # Set RNG seed
            P['seed'] = mcdc['seed']
            kernel.rng_skip_ahead(i*mcdc['event_stride'][event], P, mcdc)

            func(P, mcdc)
           
            # Update particle in the bank
            mcdc['bank']['content'][idx] = kernel.record_particle(P)
               
            # Get stack index of the next event
            next_event = P['event']
            next_stack = mcdc['stack_idx'][next_event]

            # Update stack of the next event
            idx_next_stack = mcdc['stack_'][next_stack]['size']
            mcdc['stack_'][next_stack]['content'][idx_next_stack] = idx
            mcdc['stack_'][next_stack]['size'] += 1

            # If last particle 
            if i == N-1:
                # Update main seed
                mcdc['seed'] = P['seed']

                # Reset current event stack size
                mcdc['stack_'][stack]['size'] = 0
                
                # Update hostc controller
                for j in range(mcdc['N_stack']):
                    hostco['stack_size'][j] = mcdc['stack_'][j]['size']

    if naive:
        wrap = compiler(wrap_naive, target)
    elif branching:
        wrap = compiler(wrap_branching, target)
    else:
        wrap = compiler(wrap_streaming, target)

    if target == 'cpu':
        return wrap

    # GPU-Event-based zone below
    def gpu_config(N, hostco):
        N_thread = hostco['N_thread']
        N_block = (N + (N_thread - 1)) // N_thread

        return N_block, N_thread

    #print(event)
    def hardware_wrap(mcdc, gpu_mcdc, hostco, gpu_hostco):
        nonlocal event
        nonlocal wrap
        # recorrecting event index in stack if branchless collision
        if mcdc['branchless_collision']:
            if event == 6:
                event = 4
            elif event == 5:
                event = 3
        N_block, N_thread = gpu_config(hostco['stack_size'][event], hostco)
        wrap[N_block, N_thread](gpu_mcdc, hostco)

    return hardware_wrap


# =============================================================================
# Utilities
# =============================================================================


def compiler(func, target):
    if target == 'cpu':
        return jit(func, nopython=True, nogil=True)#, parallel=True)
    elif target == 'cpus':
        return jit(func, nopython=True, nogil=True, parallel=True)
    elif target == 'gpu_device':
        return cuda.jit(func,device=True)
    elif target == 'gpu':
        return cuda.jit(func)
    else:
        print(f"[ERROR] Unrecognized target '{target}'.")

def parallel_compile(func):
    return jit(func, nopython=True, nogil=True, parallel=True)

@njit
def gpu_config(N, hostco):
    N_thread = hostco['N_thread']
    N_block = (N + (N_thread - 1)) // N_thread

    return N_block, N_thread




