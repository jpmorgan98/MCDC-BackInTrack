# MC/DC-Back In Track

Immitating key features of [MC/DC](https://github.com/CEMeNT-PSAAP/MCDC), this code repository is created to test implementations of the selected metaprogramming libraries ([Numba](https://numba.readthedocs.io/en/stable/index.html),) that are investigated in [MC/DC-TNT](https://github.com/CEMeNT-PSAAP/MCDC-TNT). This strategically helps achieving smooth integration of proposed abstraction ideas into MC/DC.

A particular goal of this repo is to demonstrate a working Python-based implementation, that supports abstractions in running mode (pure Python or Numba), MC algorithm (history-based or event-based), and kernel threading target (CPUs or GPUs). This is achieved by innovative uses of Python decorator and meta-classes, which adapt pure Python, scalar, history-based kernels into the desired running mode, MC algorithm, and threading target.

Achievements so far:
* Pure Python (history-based and event-based; only on CPU; useful for algorithm debugging)
* Numba history-based and event-based on CPU (serial)
* Numba event-based on GPU (on going)

TODO list:
1. GPU [reduction](https://numba.readthedocs.io/en/stable/cuda/reduction.html?highlight=reduction) on global/small tally (in this test code, neutron leakage). This may require designing a new adapter type.
2. Mesh tally. To implement the use of GPU [atomics](https://numba.readthedocs.io/en/stable/cuda/intrinsics.html?highlight=atomic).
3. GPU [exclusive scan](https://developer.nvidia.com/gpugems/gpugems3/part-vi-gpu-computing/chapter-39-parallel-prefix-sum-scan-cuda) for thread syncing and reproducibility. This completes branching-event adapter and allows running Numba event-based on GPU (but only with branchless collision).
4. GPU [sorting](https://developer.nvidia.com/gpugems/gpugems2/part-vi-simulation-and-numerical-algorithms/chapter-46-improved-gpu-sorting) for efficient particle bank memory access.
5. GPU adapter for multiplying events (such as fission and weight window).
6. Consolidate different types of adapter.
7. Others: Run in multiple GPUs and nodes via MPI4Py. Introduce [PyOMP](https://tigress-web.princeton.edu/~jdh4/PyOMPintro.pdf) for CPU threading. Implement [particle consolidation](https://www.sciencedirect.com/science/article/pii/S0306454917304231?via%3Dihub) in history-based for GPU run. ...
