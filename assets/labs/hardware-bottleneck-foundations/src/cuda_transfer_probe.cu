#include <cuda_runtime.h>
#include <cstdio>
#include <cstdlib>

#define CHECK(call) do { \
    cudaError_t err__ = (call); \
    if (err__ != cudaSuccess) { \
        std::fprintf(stderr, "CUDA error %s at %s:%d: %s\n", cudaGetErrorName(err__), __FILE__, __LINE__, cudaGetErrorString(err__)); \
        std::exit(2); \
    } \
} while (0)

__global__ void scale_kernel(float *x, size_t n) {
    size_t i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) x[i] = x[i] * 1.0001f + 1.0f;
}

static float elapsed_ms(cudaEvent_t start, cudaEvent_t stop) {
    CHECK(cudaEventRecord(stop));
    CHECK(cudaEventSynchronize(stop));
    float ms = 0.0f;
    CHECK(cudaEventElapsedTime(&ms, start, stop));
    return ms;
}

static void fill(float *p, size_t n) {
    for (size_t i = 0; i < n; ++i) p[i] = (float)(i % 97) * 0.25f;
}

int main() {
    int device = 0;
    CHECK(cudaSetDevice(device));
    cudaDeviceProp prop{};
    CHECK(cudaGetDeviceProperties(&prop, device));
    CHECK(cudaFree(0));  // create the CUDA context before timing rows
    const size_t sizes[] = {1u << 20, 8u << 20, 32u << 20};
    cudaEvent_t start, stop;
    CHECK(cudaEventCreate(&start));
    CHECK(cudaEventCreate(&stop));

    std::printf("{\n  \"status\": \"ok\",\n  \"device\": \"%s\",\n  \"timing_note\": \"CUDA context was initialized before timed rows; each row also performs untimed copy/kernel warmup before event timing.\",\n  \"rows\": [\n", prop.name);
    for (size_t si = 0; si < sizeof(sizes) / sizeof(sizes[0]); ++si) {
        size_t bytes = sizes[si];
        size_t n = bytes / sizeof(float);
        float *pageable = (float *)std::malloc(bytes);
        float *pinned = nullptr;
        float *device_ptr = nullptr;
        if (!pageable) return 3;
        CHECK(cudaMallocHost((void **)&pinned, bytes));
        CHECK(cudaMalloc((void **)&device_ptr, bytes));
        fill(pageable, n);
        fill(pinned, n);

        // Untimed warmup keeps the first measured row from mixing context setup,
        // page pinning/setup, or kernel JIT effects into the teaching numbers.
        CHECK(cudaMemcpy(device_ptr, pageable, bytes, cudaMemcpyHostToDevice));
        CHECK(cudaMemcpy(pageable, device_ptr, bytes, cudaMemcpyDeviceToHost));
        CHECK(cudaMemcpy(device_ptr, pinned, bytes, cudaMemcpyHostToDevice));
        CHECK(cudaMemcpy(pinned, device_ptr, bytes, cudaMemcpyDeviceToHost));
        int block = 256;
        int grid = (int)((n + block - 1) / block);
        scale_kernel<<<grid, block>>>(device_ptr, n);
        CHECK(cudaGetLastError());
        CHECK(cudaDeviceSynchronize());

        CHECK(cudaEventRecord(start));
        CHECK(cudaMemcpy(device_ptr, pageable, bytes, cudaMemcpyHostToDevice));
        float pageable_h2d_ms = elapsed_ms(start, stop);

        CHECK(cudaEventRecord(start));
        CHECK(cudaMemcpy(pageable, device_ptr, bytes, cudaMemcpyDeviceToHost));
        float pageable_d2h_ms = elapsed_ms(start, stop);

        CHECK(cudaEventRecord(start));
        CHECK(cudaMemcpy(device_ptr, pinned, bytes, cudaMemcpyHostToDevice));
        float pinned_h2d_ms = elapsed_ms(start, stop);

        CHECK(cudaEventRecord(start));
        CHECK(cudaMemcpy(pinned, device_ptr, bytes, cudaMemcpyDeviceToHost));
        float pinned_d2h_ms = elapsed_ms(start, stop);

        CHECK(cudaEventRecord(start));
        scale_kernel<<<grid, block>>>(device_ptr, n);
        CHECK(cudaGetLastError());
        float kernel_ms = elapsed_ms(start, stop);

        std::printf("    {\"bytes\": %zu, \"pageable_h2d_ms\": %.4f, \"pageable_d2h_ms\": %.4f, \"pinned_h2d_ms\": %.4f, \"pinned_d2h_ms\": %.4f, \"kernel_ms\": %.4f}%s\n",
                    bytes, pageable_h2d_ms, pageable_d2h_ms, pinned_h2d_ms, pinned_d2h_ms, kernel_ms,
                    (si + 1 == sizeof(sizes) / sizeof(sizes[0])) ? "" : ",");
        CHECK(cudaFree(device_ptr));
        CHECK(cudaFreeHost(pinned));
        std::free(pageable);
    }
    std::printf("  ]\n}\n");
    CHECK(cudaEventDestroy(start));
    CHECK(cudaEventDestroy(stop));
    return 0;
}
