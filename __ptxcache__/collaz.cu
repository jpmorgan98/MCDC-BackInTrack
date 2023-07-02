struct _16b8 { unsigned long long int data[2]; };
struct _8216b8 { unsigned long long int data[1027]; };
struct _0b8 { unsigned long long int data[0]; };
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
		_odd(fn_param_0, &prog, &fn_param_2);
	}
};
struct Even {
	using Type = void(*)(_16b8);
	template<typename PROGRAM>
	__device__ static void eval(PROGRAM prog, _16b8 fn_param_2) {
		int  dummy_void_result = 0;
		int *fn_param_0 = &dummy_void_result;
		_even(fn_param_0, &prog, &fn_param_2);
	}
};
struct collaz{
	static const size_t STASH_SIZE = 8;
	static const size_t FRAME_SIZE = 8192;
	static const size_t POOL_SIZE = 8192;
	typedef OpUnion<Odd,Even> OpSet;
	typedef _8216b8* DeviceState;
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
typedef HarmonizeProgram<collaz> collaz_hrm;
extern "C" __device__ int init_collaz_hrm(
	void*,
	void *_dev_ctx_arg,
	void *device_arg
) {
	auto _dev_ctx = (typename collaz_hrm::DeviceContext*) _dev_ctx_arg;
	auto device   = (typename collaz_hrm::DeviceState) device_arg;
	_inner_dev_init<collaz_hrm>(*_dev_ctx,device);
	return 0;
}
extern "C" __device__ int exec_collaz_hrm(
	void*,
	void   *_dev_ctx_arg,
	void   *device_arg,
	size_t  cycle_count
) {
	auto _dev_ctx = (typename collaz_hrm::DeviceContext*) _dev_ctx_arg;
	auto device   = (typename collaz_hrm::DeviceState) device_arg;
	_inner_dev_exec<collaz_hrm>(*_dev_ctx,device,cycle_count);
	return 0;
}
extern "C" __device__ 
int collaz_hrm_odd_async(void*, void* fn_param_1, void* fn_param_2){
	((collaz_hrm*)fn_param_1)->template async<Odd>(*(_16b8*)fn_param_2);
	return 0;
}
extern "C" __device__ 
int collaz_hrm_odd_sync(void*, void* fn_param_1, void* fn_param_2){
	((collaz_hrm*)fn_param_1)->template sync<Odd>(*(_16b8*)fn_param_2);
	return 0;
}
extern "C" __device__ 
int collaz_hrm_even_async(void*, void* fn_param_1, void* fn_param_2){
	((collaz_hrm*)fn_param_1)->template async<Even>(*(_16b8*)fn_param_2);
	return 0;
}
extern "C" __device__ 
int collaz_hrm_even_sync(void*, void* fn_param_1, void* fn_param_2){
	((collaz_hrm*)fn_param_1)->template sync<Even>(*(_16b8*)fn_param_2);
	return 0;
}
typedef EventProgram<collaz> collaz_evt;
extern "C" __device__ int init_collaz_evt(
	void*,
	void *_dev_ctx_arg,
	void *device_arg
) {
	auto _dev_ctx = (typename collaz_evt::DeviceContext*) _dev_ctx_arg;
	auto device   = (typename collaz_evt::DeviceState) device_arg;
	_inner_dev_init<collaz_evt>(*_dev_ctx,device);
	return 0;
}
extern "C" __device__ int exec_collaz_evt(
	void*,
	void   *_dev_ctx_arg,
	void   *device_arg,
	size_t  cycle_count
) {
	auto _dev_ctx = (typename collaz_evt::DeviceContext*) _dev_ctx_arg;
	auto device   = (typename collaz_evt::DeviceState) device_arg;
	_inner_dev_exec<collaz_evt>(*_dev_ctx,device,cycle_count);
	return 0;
}
extern "C" __device__ 
int collaz_evt_odd_async(void*, void* fn_param_1, void* fn_param_2){
	((collaz_evt*)fn_param_1)->template async<Odd>(*(_16b8*)fn_param_2);
	return 0;
}
extern "C" __device__ 
int collaz_evt_odd_sync(void*, void* fn_param_1, void* fn_param_2){
	((collaz_evt*)fn_param_1)->template sync<Odd>(*(_16b8*)fn_param_2);
	return 0;
}
extern "C" __device__ 
int collaz_evt_even_async(void*, void* fn_param_1, void* fn_param_2){
	((collaz_evt*)fn_param_1)->template async<Even>(*(_16b8*)fn_param_2);
	return 0;
}
extern "C" __device__ 
int collaz_evt_even_sync(void*, void* fn_param_1, void* fn_param_2){
	((collaz_evt*)fn_param_1)->template sync<Even>(*(_16b8*)fn_param_2);
	return 0;
}
extern "C" __device__ 
int collaz_hrm_device(void* result, void* prog){
	(*(void**)result) = ((collaz_hrm*)prog)->device;
	return 0;
}
extern "C" __device__ 
int collaz_hrm_group(void* result, void* prog){
	(*(void**)result) = ((collaz_hrm*)prog)->group;
	return 0;
}
extern "C" __device__ 
int collaz_hrm_thread(void* result, void* prog){
	(*(void**)result) = ((collaz_hrm*)prog)->thread;
	return 0;
}
extern "C" __device__ 
int collaz_hrm__dev_ctx(void* result, void* prog){
	(*(void**)result) = &((collaz_hrm*)prog)->_dev_ctx;
	return 0;
}
extern "C" __device__ 
int collaz_hrm__grp_ctx(void* result, void* prog){
	(*(void**)result) = &((collaz_hrm*)prog)->_grp_ctx;
	return 0;
}
extern "C" __device__ 
int collaz_hrm__thd_ctx(void* result, void* prog){
	(*(void**)result) = &((collaz_hrm*)prog)->_thd_ctx;
	return 0;
}
extern "C" __device__ 
int collaz_evt_device(void* result, void* prog){
	(*(void**)result) = ((collaz_evt*)prog)->device;
	return 0;
}
extern "C" __device__ 
int collaz_evt_group(void* result, void* prog){
	(*(void**)result) = ((collaz_evt*)prog)->group;
	return 0;
}
extern "C" __device__ 
int collaz_evt_thread(void* result, void* prog){
	(*(void**)result) = ((collaz_evt*)prog)->thread;
	return 0;
}
extern "C" __device__ 
int collaz_evt__dev_ctx(void* result, void* prog){
	(*(void**)result) = &((collaz_evt*)prog)->_dev_ctx;
	return 0;
}
extern "C" __device__ 
int collaz_evt__grp_ctx(void* result, void* prog){
	(*(void**)result) = &((collaz_evt*)prog)->_grp_ctx;
	return 0;
}
extern "C" __device__ 
int collaz_evt__thd_ctx(void* result, void* prog){
	(*(void**)result) = &((collaz_evt*)prog)->_thd_ctx;
	return 0;
}
