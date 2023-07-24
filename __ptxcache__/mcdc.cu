struct _48b8 { unsigned long long int data[6]; };
struct _152b8 { unsigned long long int data[19]; };
struct _0b8 { unsigned long long int data[0]; };
extern "C" __device__ int _initialize(void*, void* prog);
extern "C" __device__ int _finalize  (void*, void* prog);
extern "C" __device__ int _make_work (bool* result, void* prog);
extern "C" __device__ int _iterate(void*, void* fn_param_1, void* fn_param_2);
struct Iterate;
struct Iterate {
	using Type = void(*)(_48b8);
	template<typename PROGRAM>
	__device__ static void eval(PROGRAM prog, _48b8 fn_param_2) {
		int  dummy_void_result = 0;
		int *fn_param_0 = &dummy_void_result;
		_iterate(fn_param_0, &prog, &fn_param_2);
	}
};
struct mcdc{
	static const size_t STASH_SIZE = 8;
	static const size_t FRAME_SIZE = 8192;
	static const size_t POOL_SIZE = 8192;
	typedef OpUnion<Iterate> OpSet;
	typedef _152b8* DeviceState;
	typedef _0b8* GroupState;
	typedef _0b8* ThreadState;
	template<typename PROGRAM>
	__device__ static void initialize(PROGRAM prog) {
		int  dummy_void_result = 0;
		int *fn_param_0 = &dummy_void_result;
		_initialize(fn_param_0, &prog);
	}
	template<typename PROGRAM>
	__device__ static void finalize(PROGRAM prog) {
		int  dummy_void_result = 0;
		int *fn_param_0 = &dummy_void_result;
		_finalize(fn_param_0, &prog);
	}
	template<typename PROGRAM>
	__device__ static bool make_work(PROGRAM prog) {
		bool  result;
		bool *fn_param_0 = &result;
		_make_work(fn_param_0, &prog);
		return result;
	}
};
