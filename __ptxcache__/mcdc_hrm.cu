#include "mcdc.cu"
typedef HarmonizeProgram<mcdc> mcdc_hrm;
extern "C" __device__ int init_program(
	void*,
	void *_dev_ctx_arg,
	void *device_arg
) {
	auto _dev_ctx = (typename mcdc_hrm::DeviceContext*) _dev_ctx_arg;
	auto device   = (typename mcdc_hrm::DeviceState) device_arg;
	_inner_dev_init<mcdc_hrm>(*_dev_ctx,device);
	return 0;
}
extern "C" __device__ int exec_program(
	void*,
	void   *_dev_ctx_arg,
	void   *device_arg,
	size_t  cycle_count
) {
	auto _dev_ctx = (typename mcdc_hrm::DeviceContext*) _dev_ctx_arg;
	auto device   = (typename mcdc_hrm::DeviceState) device_arg;
	_inner_dev_exec<mcdc_hrm>(*_dev_ctx,device,cycle_count);
	return 0;
}
extern "C" __device__ 
int dispatch_iterate_async(void*, void* fn_param_1, void* fn_param_2){
	((mcdc_hrm*)fn_param_1)->template async<Iterate>(*(_48b8*)fn_param_2);
	return 0;
}
extern "C" __device__ 
int dispatch_iterate_sync(void*, void* fn_param_1, void* fn_param_2){
	((mcdc_hrm*)fn_param_1)->template sync<Iterate>(*(_48b8*)fn_param_2);
	return 0;
}
extern "C" __device__ 
int access_device(void* result, void* prog){
	(*(void**)result) = ((mcdc_hrm*)prog)->device;
	return 0;
}
extern "C" __device__ 
int access_group(void* result, void* prog){
	(*(void**)result) = ((mcdc_hrm*)prog)->group;
	return 0;
}
extern "C" __device__ 
int access_thread(void* result, void* prog){
	(*(void**)result) = ((mcdc_hrm*)prog)->thread;
	return 0;
}
