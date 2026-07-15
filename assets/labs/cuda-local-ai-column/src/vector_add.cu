#include <cuda_runtime.h>
#include <cstdio>

__global__ void vector_add(const float* a, const float* b, float* c, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) c[i] = a[i] + b[i];
}

int main() {
    const int n = 16;
    float a[n], b[n], c[n];
    for (int i = 0; i < n; ++i) { a[i] = float(i); b[i] = float(2 * i); }
    float *da, *db, *dc;
    cudaMalloc(&da, n * sizeof(float));
    cudaMalloc(&db, n * sizeof(float));
    cudaMalloc(&dc, n * sizeof(float));
    cudaMemcpy(da, a, n * sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(db, b, n * sizeof(float), cudaMemcpyHostToDevice);
    vector_add<<<(n + 7) / 8, 8>>>(da, db, dc, n);
    cudaMemcpy(c, dc, n * sizeof(float), cudaMemcpyDeviceToHost);
    cudaDeviceSynchronize();
    for (int i = 0; i < n; ++i) if (c[i] != a[i] + b[i]) return 2;
    std::printf("vector_add_ok n=%d last=%.1f\n", n, c[n-1]);
    cudaFree(da); cudaFree(db); cudaFree(dc);
    return 0;
}
