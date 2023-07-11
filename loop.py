import numpy as np
import type_, kernel, adapter

from numba import objmode, jit, prange, cuda

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
    print('Location A')
    kernel.initialize_stack[adapter.gpu_config(mcdc['N_particle'], hostco)](mcdc, hostco)
    #else:
    #kernel.initialize_stack(mcdc, hostco)
    #kernel.initialize_stack[adapter.gpu_config(mcdc['N_particle'], hostco)](mcdc, hostco)
        
    # =========================================================================
    # Simulation loop
    # =========================================================================
    print('To simulation')
    it = 0
    while np.max(hostco['stack_size'][1:]) > 0:
        it += 1
        # =====================================================================
        # Initialize event
        # =====================================================================
    
        # Determine next event executed based on the longest stack
        stack = np.argmax(hostco['stack_size'][1:]) + 1 # Offset for EVENT_NONE
        event = hostco['event_idx'][stack]

        #print(event)

        # =================================================================
        # Event loop
        # =================================================================
        
        if event == EVENT_SOURCE:
            #print('Source! {}'.format(event))
            kernel.source(mcdc, hostco, event)
        elif event == EVENT_MOVE:
            #print('Source! {}'.format(event))
            kernel.move(mcdc, hostco, event)
        elif event == EVENT_SCATTERING:
            #print('Source! {}'.format(event))
            kernel.scattering(mcdc, hostco, event)
        elif event == EVENT_FISSION:
            #print('Source! {}'.format(event))
            kernel.fission(mcdc, hostco, event)
        elif event == EVENT_LEAKAGE:
            #print('Source! {}'.format(event))
            kernel.leakage(mcdc, hostco, event)
        elif event == EVENT_BRANCHLESS_COLLISION:
            print('Branchless Collision!', event)
            kernel.branchless_collision(mcdc, hostco, event)

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




def ASYNC_simulation(mcdc, hostco):



    # =========================================================================
    # Simulation loop
    # =========================================================================
    print('To simulation')
    it = 0
    while np.max(hostco['stack_size'][1:]) > 0:
        it += 1
        # =====================================================================
        # Initialize event
        # =====================================================================
    
        # Determine next event executed based on the longest stack
        stack = np.argmax(hostco['stack_size'][1:]) + 1 # Offset for EVENT_NONE
        event = hostco['event_idx'][stack]

        #print(event)

        # =================================================================
        # Event loop
        # =================================================================
        
        if event == EVENT_SOURCE:
            #print('Source! {}'.format(event))
            kernel.source(mcdc, hostco, event)
        elif event == EVENT_MOVE:
            #print('Source! {}'.format(event))
            kernel.move(mcdc, hostco, event)
        elif event == EVENT_SCATTERING:
            #print('Source! {}'.format(event))
            kernel.scattering(mcdc, hostco, event)
        elif event == EVENT_FISSION:
            #print('Source! {}'.format(event))
            kernel.fission(mcdc, hostco, event)
        elif event == EVENT_LEAKAGE:
            #print('Source! {}'.format(event))
            kernel.leakage(mcdc, hostco, event)
        elif event == EVENT_BRANCHLESS_COLLISION:
            print('Branchless Collision!', event)
            kernel.branchless_collision(mcdc, hostco, event)



# =============================================================================
# Factory
# =============================================================================

def make_loops(alg, target):
    global simulation
    if alg == 'history':
        simulation = adapter.loop(HISTORY_simulation, target)
    elif alg == "async":
        simulation = adapter.loop(ASYNC_simulation,   target)
    else:
        simulation = adapter.loop(EVENT_simulation,   target)
