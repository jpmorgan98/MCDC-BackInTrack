
import numpy as np
from numba import cuda
import numba
import harm



val_count = 10
dev_state_type = numba.from_dtype(np.dtype([ ('val',np.dtype((np.uintp,val_count+1))) ]))
grp_state_type = numba.from_dtype(np.dtype([ ]))
thd_state_type = numba.from_dtype(np.dtype([ ]))


collaz_iter_dtype = np.dtype([('value',np.int32), ('start',np.int32), ('steps',np.int32)])
collaz_iter = numba.from_dtype(collaz_iter_dtype)

sig = numba.types.void(numba.uintp,collaz_iter)

dev_sig = dev_state_type(numba.uintp)



def even(prog: numba.uintp, iter: collaz_iter):
    iter['steps'] += 1
    iter['value'] /= 2
    if iter['value'] % 2 == 0:
        even_async(prog,iter)
    else :
        odd_async(prog,iter)


def odd(prog: numba.uintp, iter: collaz_iter):
    if iter['value'] <= 1:
        device(prog)['val'][1+iter['start']] = iter['steps']
    else:
        iter['value'] = iter['value'] * 3 + 1
        iter['steps'] += 1
        if iter['value'] % 2 == 0:
            even_async(prog,iter)
        else :
            odd_async(prog,iter)


def initialize(prog: numba.uintp):
    pass

def finalize(prog: numba.uintp):
    pass

def make_work(prog: numba.uintp) -> numba.boolean:
    old = numba.cuda.atomic.add(device(prog)['val'],0,1)
    if old >= val_count:
        return False

    #numba.cuda.atomic.add(device(prog)['val'],1+old,old)
    iter = numba.cuda.local.array(1,collaz_iter)
    iter[0]['value'] = old
    iter[0]['start'] = old
    iter[0]['steps'] = 0

    if old % 2 == 0:
        even_async(prog,iter[0])
    else:
        odd_async(prog,iter[0])
    return True


base_fns   = (initialize,finalize,make_work)
state_spec = (dev_state_type,grp_state_type,thd_state_type) 
async_fns  = [odd,even]

device, group, thread = harm.RuntimeSpec.access_fns(state_spec)
odd_async, even_async = harm.RuntimeSpec.async_dispatch(odd,even)

collaz_spec = harm.RuntimeSpec("collaz",state_spec,base_fns,async_fns)

runtime = collaz_spec.instance()

runtime.init(1024)

runtime.exec(6553600)

state = runtime.load_state()
print(state)

def collaz_check(value):
    step = 0
    while value > 1:
        step += 1
        if value % 2 == 0:
            value /= 2
        else :
            value = value * 3 + 1
    return step

total = 0
for val in range(val_count):
    steps = collaz_check(val)
    total += steps
    print(steps,end=", ")
print("")
print(f"Total: {total}")
