import numpy as np

from constant import *

float64 = np.float64
int64   = np.int64
uint64  = np.uint64
bool_   = np.bool_

# =============================================================================
# Particles
# =============================================================================

# Particle (in-flight)
particle = np.dtype([('x', float64), ('ux', float64), ('w', float64),
                     ('seed', int64), ('event', int64), ('alive', bool_)])
                     #,('padA',np.uint8), ('padB', np.uint16), ('padC', np.uint32)])

# Particle record (in-bank/stack)
particle_rec = np.dtype([('x', float64), ('ux', float64), ('w', float64)])

# Particle bank
def get_type_bank(max_size):
    return np.dtype([('content', particle_rec, (max_size,)), ('size', int64)])

# =============================================================================
# Event-based stack of particle indices
# =============================================================================

def get_type_stack(max_size):
    return np.dtype([('content', int64, (max_size,)), ('size', int64)])

# =============================================================================
# Host controller (necessary for GPU run)
# =============================================================================

def get_hostco(N_stack):
    the_type = np.dtype([('N_thread', int64), 
                         ('stack_size', int64, (N_stack,)),
                         ('event_idx', int64, (N_stack,))])
    return np.zeros(1, dtype=the_type)[0]

# =============================================================================
# Global data
# =============================================================================

global_ = None
def make_type_global(N_particle, N_stack, alg):
    global global_

    struct = [('N_history', int64), ('N_particle', int64), ('N_stack', int64),

              ('SigmaC', float64), ('SigmaS', float64), ('SigmaF', float64),
              ('nu', float64), ('SigmaT', float64), ('X', float64),
              ('tally', float64, (3,)), 
              
              ('rng_g', int64), ('rng_c', int64), ('rng_mod', uint64),
              ('seed', int64),  ('N_thread', int64)]

    
    # ======================================
    # Bank and stack
    # ======================================
    if alg in [ 'async', 'async-multi', 'new-event', 'new-event-multi' ]:
        struct += [('source_counter',int64,(1,))]
    else:
        struct += [
                   ('history_stride', int64),
                   ('event_stride', int64, (N_EVENT,)),

                   ('stack_idx', int64, (N_EVENT,)),
                   ('event_idx', int64, (N_stack,))]


        # Sizes
        if alg == 'history':
            bank_size  = 100000
            stack_size = 0
        else:
            bank_size  = int(2*N_particle)
            stack_size = int(2*N_particle)

        type_stack = get_type_bank(stack_size)
        struct += [('bank', get_type_bank(bank_size)), 
                ('stack_', get_type_stack(stack_size), (N_stack,))]

        # ======================================

        # Secondaries parameters for sync in branching event
        struct += [('secondaries_stack', int64, (stack_size,)),
                ('secondaries_counter', int64, (stack_size, N_stack)),
                ('secondaries_idx', int64, (stack_size, N_stack))]

    # Bool-typed (TODO: report bug)
    struct += [('history_based', bool_), ('gpu', bool_), 
            ('branchless_collision', bool_)]

    global_ = np.dtype(struct)
