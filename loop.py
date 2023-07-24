import numpy as np
import type_, kernel, adapter

import adapter

from adapter import gpu_config

import numba
from numba import objmode, njit, jit, prange, cuda

from constant import *

simulation = None

# =============================================================================
# History-based
# =============================================================================

#@jit(nopython=True)
def HISTORY_simulation(mcdc, hostco):
    # =========================================================================
    # Simulation loop
    # =========================================================================

    for i_history in prange(mcdc['N_history']):
        # =====================================================================
        # Initialize history
        # =====================================================================

        # Create particle
        P = kernel.create(type_.particle)

        # Set RNG seed
        P['seed'] = mcdc['seed']
        kernel.rng_skip_ahead(i_history*mcdc['history_stride'], P, mcdc)

        # Initialize particle
        kernel.source(P, mcdc)
        
        # "Push" to the bank
        mcdc['bank']['content'][0] = kernel.record_particle(P)
        mcdc['bank']['size']       = 1

        # Reset main seed
        mcdc['seed'] = P['seed']

        # =====================================================================
        # History loop
        # =====================================================================

        while mcdc['bank']['size'] > 0:
            # =================================================================
            # Initialize particle
            # =================================================================

            # "Pop" particle from bank
            mcdc['bank']['size'] -= 1
            idx = mcdc['bank']['size']
            P = kernel.read_particle(mcdc['bank']['content'][idx])

            # Set particle seed
            P['seed'] = mcdc['seed']

            # =================================================================
            # Particle loop
            # =================================================================

            # Particle loop
            while P['alive']:
                # Move to event
                kernel.move(P, mcdc)

                # Event
                event = P['event']

                # Collision
                if event == EVENT_SCATTERING:
                    kernel.scattering(P, mcdc)
                elif event == EVENT_FISSION:
                    kernel.fission(P, mcdc)
                elif event == EVENT_LEAKAGE:
                    kernel.leakage(P, mcdc)
                elif event == EVENT_BRANCHLESS_COLLISION:
                    kernel.branchless_collision(P, mcdc)

            # Update main seed
            mcdc['seed'] = P['seed']

# =============================================================================
# Event-based
# =============================================================================

#init_stack = None

def EVENT_simulation(mcdc, hostco):
    # =========================================================================
    # Initialize simulation
    # =========================================================================
    #init_stack = None
    #if mcdc['gpu']:
    #print('Location A')
    #kernel.initialize_stack(mcdc,hostco)
    #else:
    #!kernel.initialize_stack(mcdc, hostco)
    
    #b,t = adapter.gpu_config(mcdc['N_particle'], hostco)
    b,t = adapter.gpu_config(int(1E6), hostco)
    gpu_hostco = cuda.to_device(hostco)
    gpu_mcdc   = cuda.to_device(mcdc)
    kernel.initialize_stack[b,t](gpu_mcdc, gpu_hostco)
        
    # =========================================================================
    # Simulation loop
    # =========================================================================
    #print('To simulation')
    it = 0
    while np.max(hostco['stack_size'][1:]) > 0:
        it += 1
        #print(it)
        # =====================================================================
        # Initialize event
        # =====================================================================
    
        # Determine next event executed based on the longest stack
        #gpu_hostco.copy_to_host(hostco)
        stack = np.argmax(hostco['stack_size'][1:]) + 1 # Offset for EVENT_NONE
        event = hostco['event_idx'][stack]

        #print(event)

        # =================================================================
        # Event loop
        # =================================================================
        
        if event == EVENT_SOURCE:
            #print('Source! {}'.format(event))
            kernel.source(mcdc, gpu_mcdc, hostco, gpu_hostco)
        elif event == EVENT_MOVE:
            #print('Move! {}'.format(event))
            kernel.move(mcdc, gpu_mcdc, hostco,  gpu_hostco)
        elif event == EVENT_SCATTERING:
            #print('Scattering! {}'.format(event))
            kernel.scattering(mcdc, gpu_mcdc, hostco, gpu_hostco)
        elif event == EVENT_FISSION:
            #print('Fission! {}'.format(event))
            kernel.fission(mcdc, gpu_mcdc, hostco, gpu_hostco)
        elif event == EVENT_LEAKAGE:
            #print('Leak! {}'.format(event))
            kernel.leakage(mcdc, gpu_mcdc, hostco, gpu_hostco)
        elif event == EVENT_BRANCHLESS_COLLISION:
            #print('Branchless Collision!', event)
            kernel.branchless_collision(mcdc, gpu_mcdc, hostco, gpu_hostco)


        '''
        print(hostco['stack_size'])
        print(mcdc['stack_']['size'])
        for i in range(hostco['stack_size'].shape[0]):
            size = mcdc['stack_'][i]['size']
            if size > 0:
                print(i, size, mcdc['stack_'][i]['content'][:size])
        print(mcdc['bank'])
        print('\n\n')
        '''

    gpu_mcdc.copy_to_host(mcdc)

path_to_harmonize='../harmonize-code'
import sys
sys.path.append(path_to_harmonize)
import harmonize as harm
def ASYNC_simulation_factory(single_fn=True, asynchronous=True):

    val_count = 65536*2
    dev_state_type = numba.from_dtype(type_.global_)
    grp_state_type = numba.from_dtype(np.dtype([ ]))
    thd_state_type = numba.from_dtype(np.dtype([ ]))

    particle = numba.from_dtype(type_.particle)

    def initialize(prog: numba.uintp):
        pass

    def finalize(prog: numba.uintp):
        pass


    def continuation(prog: numba.uintp, P: particle):
        if   P['event'] == EVENT_SOURCE:
            source_async(prog,P)
        elif P['event'] == EVENT_MOVE:
            move_async(prog,P)
        elif P['event'] == EVENT_SCATTERING:
            scattering_async(prog,P)
        elif P['event'] == EVENT_FISSION:
            fission_async(prog,P)
        elif P['event'] == EVENT_LEAKAGE:
            leakage_async(prog,P)
        elif P['event'] == EVENT_BRANCHLESS_COLLISION:
            bcollision_async(prog,P)


    def source(prog: numba.uintp, P: particle):
        kernel.source(P, device(prog))
        continuation(prog,P)
    
    def move(prog: numba.uintp, P: particle):
        kernel.move(P, device(prog))
        continuation(prog,P)
        
    def scattering(prog: numba.uintp, P: particle):
        kernel.scattering(P, device(prog))
        continuation(prog,P)
        
    def fission(prog: numba.uintp, P: particle):
        n = kernel.fission(P, device(prog))
        for i in range(n):
            P_new       = numba.cuda.local.array(1,particle)[0]
            P_new['x']  = P['x']
            P_new['ux'] = -1.0 + 2.0*kernel.rng(P, device(prog))
            P_new['w']  = P['w']
            P_new['seed']  = P['seed']
            P_new['event'] = EVENT_MOVE
            P_new['alive'] = True
            continuation(prog,P_new)
        kernel.terminate_particle(P)
        
    def leakage(prog: numba.uintp, P: particle):
        kernel.leakage(P, device(prog))
        continuation(prog,P)
        
    def bcollision(prog: numba.uintp, P: particle):
        kernel.branchless_collision(P, device(prog))
        continuation(prog,P)


    def iterate(prog: numba.uintp, P: particle):
        if   P['event'] == EVENT_SOURCE:
            kernel.source(P, device(prog))
        elif P['event'] == EVENT_MOVE:
            kernel.move(P, device(prog))
        elif P['event'] == EVENT_SCATTERING:
            kernel.scattering(P, device(prog))
        elif P['event'] == EVENT_FISSION:
            n = kernel.fission(P, device(prog))
            for i in range(n):
                P_new       = numba.cuda.local.array(1,particle)[0]
                P_new['x']  = P['x']
                P_new['ux'] = -1.0 + 2.0*kernel.rng(P, device(prog))
                P_new['w']  = P['w']
                P_new['seed']  = P['seed']
                P_new['event'] = EVENT_MOVE
                P_new['alive'] = True
                iterate_async(prog,P_new)
            kernel.terminate_particle(P)
        elif P['event'] == EVENT_LEAKAGE:
            kernel.leakage(P, device(prog))
        elif P['event'] == EVENT_BRANCHLESS_COLLISION:
            kernel.branchless_collision(P, device(prog))

        if   P['event'] != EVENT_NONE:
            iterate_async(prog,P)


    state_spec = (dev_state_type,grp_state_type,thd_state_type) 
    one_event_fns   = [iterate]
    multi_event_fns = [source,move,scattering,fission,leakage,bcollision]

    device, group, thread = harm.RuntimeSpec.access_fns(state_spec)
    iterate_async, = harm.RuntimeSpec.async_dispatch(iterate)
    source_async, move_async, scattering_async, fission_async, leakage_async, bcollision_async = \
    harm.RuntimeSpec.async_dispatch(source,move,scattering,fission,leakage,bcollision)
    
    continuation = adapter.compiler(continuation,"gpu_device")

    program_spec = None
    
    if single_fn:
        def make_work(prog: numba.uintp) -> numba.boolean:
            N_particle = device(prog)['N_particle']
            index = numba.cuda.atomic.add(device(prog)['source_counter'],0,1)
            if index >= N_particle:
                return False
            
            new_particle = numba.cuda.local.array(1,particle)[0]
            new_particle['event'] = EVENT_SOURCE
            new_particle['seed']  = index
            iterate_async(prog,new_particle)
            return True

        base_fns   = (initialize,finalize,make_work)
        program_spec = harm.RuntimeSpec("mcdc",state_spec,base_fns,one_event_fns,WORK_ARENA_SIZE=655360)
    else:
        def make_work(prog: numba.uintp) -> numba.boolean:
            N_particle = device(prog)['N_particle']
            index = numba.cuda.atomic.add(device(prog)['source_counter'],0,1)
            if index >= N_particle:
                return False
            
            new_particle = numba.cuda.local.array(1,particle)[0]
            new_particle['event'] = EVENT_SOURCE
            new_particle['seed']  = index
            source_async(prog,new_particle)
            return True

        base_fns   = (initialize,finalize,make_work)
        program_spec = harm.RuntimeSpec("mcdc",state_spec,base_fns,multi_event_fns,WORK_ARENA_SIZE=655360)

    if asynchronous:
        runtime = program_spec.harmonize_instance()
    else:
        runtime = program_spec.event_instance(io_capacity=65536*4,load_margin=1024)

    def runner(mcdc,hostco):
        runtime.init(4096)
        runtime.store_state(mcdc)
        if asynchronous:
            runtime.exec(655360,4096)
        else:
            runtime.exec(4,4096)
        runtime.load_state(mcdc)

    return runner






# =============================================================================
# Factory
# =============================================================================

def make_loops(alg, target):
    global simulation
    if alg == 'history':
        simulation = adapter.loop(HISTORY_simulation, target)
    elif alg == 'event':
        simulation = adapter.loop(EVENT_simulation,   target)
    elif alg == 'async':
        simulation = ASYNC_simulation_factory(True,True)
    else:
        print(f"[ERROR] Unrecognized algorithm type '{alg}'")
