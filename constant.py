# RNG
RNG_SEED   = 1
RNG_STRIDE = 152917
RNG_G      = 2806196910506780709
RNG_C      = 1
RNG_MOD    = 2**63

# EVENT
EVENT_NONE                 = 0 # Particle is dead
EVENT_SOURCE               = 1
EVENT_MOVE                 = 2
EVENT_SCATTERING           = 3
EVENT_FISSION              = 4
EVENT_LEAKAGE              = 5
EVENT_BRANCHLESS_COLLISION = 6
N_EVENT                    = 7

float64 = np.float64
int64   = np.int64
uint64  = np.uint64
bool_   = np.bool_
