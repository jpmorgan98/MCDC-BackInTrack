
extern __device__ int simple(long int *z, int x, int y);


template<bool B>
__device__ void simple_kernel_inner() {
    int x = threadIdx.x;
    int y = 0;
    long int z = 0;
    simple(&z,x,y);
    if(B) {
        printf("(%d,%ld)\n",threadIdx.x,z);
    }
}


// nvcc harm.cu -rdc true -ptx -o harm.ptx

extern "C" __device__
int simple_kernel(void* result) {
    simple_kernel_inner<true>();
    return 0;
}

