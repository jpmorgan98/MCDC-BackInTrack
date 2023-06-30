
struct sneaky {
	MCDCContext* mcdc_context;
	MyContext*   my_context;
};


__device__ void* preamble(void* ptr) {
	void** offset_ptr = (void**)ptr;
	return offset_ptr[-1];
}
struct _88b8 { unsigned long long int data[11]; };
struct _16b8 { unsigned long long int data[2]; };
extern "C" __device__ int _initialize(void*, void* prog);
extern "C" __device__ int _finalize  (void*, void* prog);
extern "C" __device__ int _make_work (bool* result, void* prog);
extern "C" __device__ int _odd(void*, void* fn_param_1, void* fn_param_2);
extern "C" __device__ int _even(void*, void* fn_param_1, void* fn_param_2);
struct Odd;
struct Even;
struct Odd {
	using Type = void(*)(_16b8);
	template<typename PROGRAM>
	__device__ static void eval(PROGRAM prog, _16b8 fn_param_2) {
		int  dummy_void_result = 0;
		int *fn_param_0 = &dummy_void_result;
	printf("{odd}");
		_odd(fn_param_0, &prog.device, &fn_param_2);
	}
};
struct Even {
	using Type = void(*)(_16b8);
	template<typename PROGRAM>
	__device__ static void eval(PROGRAM prog, _16b8 fn_param_2) {
		int  dummy_void_result = 0;
		int *fn_param_0 = &dummy_void_result;
	printf("{even}");
		_even(fn_param_0, &prog.device, &fn_param_2);
	}
};
struct collaz{
	static const size_t STASH_SIZE = 8;
	static const size_t FRAME_SIZE = 8192;
	static const size_t POOL_SIZE = 8192;
	typedef OpUnion<Odd,Even> OpSet;
	typedef _88b8* DeviceState;
	typedef int32_t GroupState;
	typedef int16_t ThreadState;
	template<typename PROGRAM>
	__device__ static void initialize(PROGRAM prog) {
		int  dummy_void_result = 0;
		int *fn_param_0 = &dummy_void_result;
	printf("{initialize}");
		_initialize(fn_param_0, &prog.device);
	}
	template<typename PROGRAM>
	__device__ static void finalize(PROGRAM prog) {
		int  dummy_void_result = 0;
		int *fn_param_0 = &dummy_void_result;
	printf("{finalize}");
		_finalize(fn_param_0, &prog.device);
	}
	template<typename PROGRAM>
	__device__ static bool make_work(PROGRAM prog) {
		bool  result;
		bool *fn_param_0 = &result;
	printf("{make_work}");
		_make_work(fn_param_0, &prog.device);
		return result;
	}
};
typedef HarmonizeProgram<collaz> collaz_hrm;
extern "C" __device__ int init_collaz_hrm(
	void*,
	void *_dev_ctx_arg,
	void *device_arg
) {
	auto _dev_ctx = (typename collaz_hrm::DeviceContext*) _dev_ctx_arg;
	auto device   = (typename collaz_hrm::DeviceState*) device_arg;
	_inner_dev_init<collaz_hrm>(*_dev_ctx,*device);
	return 0;
}
extern "C" __device__ int exec_collaz_hrm(
	void*,
	void   *_dev_ctx_arg,
	void   *device_arg,
	size_t  cycle_count
) {
	auto _dev_ctx = (typename collaz_hrm::DeviceContext*) _dev_ctx_arg;
	auto device   = (typename collaz_hrm::DeviceState*) device_arg;
	printf("<ctx%p>",_dev_ctx);
	printf("<sta%p>",device);
	printf("<pre%p>",preamble(device));
	_inner_dev_exec<collaz_hrm>(*_dev_ctx,*device,cycle_count);
	return 0;
}
extern "C" __device__ 
int collaz_hrm_odd_async(void*, void* fn_param_1, void* fn_param_2){
	printf("{ odd trampoline }");
	printf("<sta%p>",fn_param_1);
	printf("<pre%p>",preamble(fn_param_1));
	void* prog = preamble(fn_param_1);
	((collaz_hrm*)prog)->template async<Odd>(*(_16b8*)fn_param_2);
	return 0;
}
extern "C" __device__ 
int collaz_hrm_odd_sync(void*, void* fn_param_1, void* fn_param_2){
	printf("{ odd trampoline }");
	printf("<sta%p>",fn_param_1);
	printf("<pre%p>",preamble(fn_param_1));
	void* prog = preamble(fn_param_1);
	((collaz_hrm*)prog)->template sync<Odd>(*(_16b8*)fn_param_2);
	return 0;
}
extern "C" __device__ 
int collaz_hrm_even_async(void*, void* fn_param_1, void* fn_param_2){
	printf("{ even trampoline }");
	printf("<sta%p>",fn_param_1);
	printf("<pre%p>",preamble(fn_param_1));
	void* prog = preamble(fn_param_1);
	((collaz_hrm*)prog)->template async<Even>(*(_16b8*)fn_param_2);
	return 0;
}
extern "C" __device__ 
int collaz_hrm_even_sync(void*, void* fn_param_1, void* fn_param_2){
	printf("{ even trampoline }");
	printf("<sta%p>",fn_param_1);
	printf("<pre%p>",preamble(fn_param_1));
	void* prog = preamble(fn_param_1);
	((collaz_hrm*)prog)->template sync<Even>(*(_16b8*)fn_param_2);
	return 0;
}
typedef EventProgram<collaz> collaz_evt;
extern "C" __device__ int init_collaz_evt(
	void*,
	void *_dev_ctx_arg,
	void *device_arg
) {
	auto _dev_ctx = (typename collaz_evt::DeviceContext*) _dev_ctx_arg;
	auto device   = (typename collaz_evt::DeviceState*) device_arg;
	_inner_dev_init<collaz_evt>(*_dev_ctx,*device);
	return 0;
}
extern "C" __device__ int exec_collaz_evt(
	void*,
	void   *_dev_ctx_arg,
	void   *device_arg,
	size_t  cycle_count
) {
	auto _dev_ctx = (typename collaz_evt::DeviceContext*) _dev_ctx_arg;
	auto device   = (typename collaz_evt::DeviceState*) device_arg;
	printf("<ctx%p>",_dev_ctx);
	printf("<sta%p>",device);
	printf("<pre%p>",preamble(device));
	_inner_dev_exec<collaz_evt>(*_dev_ctx,*device,cycle_count);
	return 0;
}
extern "C" __device__ 
int collaz_evt_odd_async(void*, void* fn_param_1, void* fn_param_2){
	printf("{ odd trampoline }");
	printf("<sta%p>",fn_param_1);
	printf("<pre%p>",preamble(fn_param_1));
	void* prog = preamble(fn_param_1);
	((collaz_evt*)prog)->template async<Odd>(*(_16b8*)fn_param_2);
	return 0;
}
extern "C" __device__ 
int collaz_evt_odd_sync(void*, void* fn_param_1, void* fn_param_2){
	printf("{ odd trampoline }");
	printf("<sta%p>",fn_param_1);
	printf("<pre%p>",preamble(fn_param_1));
	void* prog = preamble(fn_param_1);
	((collaz_evt*)prog)->template sync<Odd>(*(_16b8*)fn_param_2);
	return 0;
}
extern "C" __device__ 
int collaz_evt_even_async(void*, void* fn_param_1, void* fn_param_2){
	printf("{ even trampoline }");
	printf("<sta%p>",fn_param_1);
	printf("<pre%p>",preamble(fn_param_1));
	void* prog = preamble(fn_param_1);
	((collaz_evt*)prog)->template async<Even>(*(_16b8*)fn_param_2);
	return 0;
}
extern "C" __device__ 
int collaz_evt_even_sync(void*, void* fn_param_1, void* fn_param_2){
	printf("{ even trampoline }");
	printf("<sta%p>",fn_param_1);
	printf("<pre%p>",preamble(fn_param_1));
	void* prog = preamble(fn_param_1);
	((collaz_evt*)prog)->template sync<Even>(*(_16b8*)fn_param_2);
	return 0;
}
