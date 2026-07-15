#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <inttypes.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static volatile double g_sink_double = 0.0;
static volatile uint64_t g_sink_u64 = 0;

static double now_seconds(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) {
        perror("clock_gettime");
        exit(2);
    }
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1000000000.0;
}

static void *xaligned_alloc(size_t alignment, size_t bytes) {
    void *ptr = NULL;
    int rc = posix_memalign(&ptr, alignment, bytes);
    if (rc != 0) {
        fprintf(stderr, "posix_memalign failed: %s\n", strerror(rc));
        exit(3);
    }
    memset(ptr, 0, bytes);
    return ptr;
}

static double mib_per_s(size_t bytes, double seconds) {
    if (seconds <= 0.0) return 0.0;
    return ((double)bytes / (1024.0 * 1024.0)) / seconds;
}

static void emit_row(const char *experiment, const char *variant, size_t work_items, size_t useful_bytes, double seconds, double checksum) {
    printf("%s,%s,%zu,%zu,%.9f,%.3f,%.6f\n", experiment, variant, work_items, useful_bytes, seconds, mib_per_s(useful_bytes, seconds), checksum);
}

static void matrix_locality(void) {
    const size_t n = 1024;
    const size_t reps = 10;
    const size_t total = n * n;
    double *a = (double *)xaligned_alloc(64, total * sizeof(double));
    for (size_t i = 0; i < total; ++i) a[i] = (double)((i % 97) + 1) * 0.25;

    double sum = 0.0;
    double t0 = now_seconds();
    for (size_t r = 0; r < reps; ++r) {
        for (size_t row = 0; row < n; ++row) {
            size_t base = row * n;
            for (size_t col = 0; col < n; ++col) sum += a[base + col];
        }
    }
    double row_seconds = now_seconds() - t0;
    g_sink_double = sum;
    emit_row("matrix_locality", "row_major", total * reps, total * reps * sizeof(double), row_seconds, sum);

    sum = 0.0;
    t0 = now_seconds();
    for (size_t r = 0; r < reps; ++r) {
        for (size_t col = 0; col < n; ++col) {
            for (size_t row = 0; row < n; ++row) sum += a[row * n + col];
        }
    }
    double col_seconds = now_seconds() - t0;
    g_sink_double = sum;
    emit_row("matrix_locality", "column_major", total * reps, total * reps * sizeof(double), col_seconds, sum);
    free(a);
}

static void stride_scan(void) {
    const size_t n = 8u * 1024u * 1024u;
    const size_t reps = 5;
    double *a = (double *)xaligned_alloc(64, n * sizeof(double));
    for (size_t i = 0; i < n; ++i) a[i] = (double)((i * 17u) & 255u) + 0.5;
    const size_t strides[] = {1, 2, 4, 8, 16, 32, 64, 128, 256};
    for (size_t s = 0; s < sizeof(strides) / sizeof(strides[0]); ++s) {
        size_t stride = strides[s];
        double sum = 0.0;
        double t0 = now_seconds();
        size_t visits = 0;
        for (size_t r = 0; r < reps; ++r) {
            for (size_t i = 0; i < n; i += stride) {
                sum += a[i];
                ++visits;
            }
        }
        double seconds = now_seconds() - t0;
        g_sink_double = sum;
        char name[32];
        snprintf(name, sizeof(name), "stride_%zu", stride);
        emit_row("stride_scan", name, visits, visits * sizeof(double), seconds, sum);
    }
    free(a);
}

static uint32_t lcg(uint32_t *state) {
    *state = (*state * 1664525u) + 1013904223u;
    return *state;
}

__attribute__((noinline)) static uint64_t branch_accumulate(const uint32_t *values, size_t n, size_t reps) {
    uint64_t acc = 0;
    for (size_t r = 0; r < reps; ++r) {
        for (size_t i = 0; i < n; ++i) {
            if (values[i] & 1u) acc += (uint64_t)(values[i] & 1023u);
            else acc -= (uint64_t)(values[i] & 1023u);
        }
    }
    return acc;
}

static void branch_predictability(void) {
    const size_t n = 16u * 1024u * 1024u;
    const size_t reps = 4;
    uint32_t *predictable = (uint32_t *)xaligned_alloc(64, n * sizeof(uint32_t));
    uint32_t *unpredictable = (uint32_t *)xaligned_alloc(64, n * sizeof(uint32_t));
    uint32_t state = 0xC0FFEEu;
    for (size_t i = 0; i < n; ++i) {
        predictable[i] = (uint32_t)(2u * (i & 511u));
        unpredictable[i] = lcg(&state);
    }

    double t0 = now_seconds();
    uint64_t acc = branch_accumulate(predictable, n, reps);
    double predictable_seconds = now_seconds() - t0;
    g_sink_u64 = acc;
    emit_row("branch_predictability", "predictable_even", n * reps, n * reps * sizeof(uint32_t), predictable_seconds, (double)acc);

    t0 = now_seconds();
    acc = branch_accumulate(unpredictable, n, reps);
    double unpredictable_seconds = now_seconds() - t0;
    g_sink_u64 = acc;
    emit_row("branch_predictability", "unpredictable_lcg", n * reps, n * reps * sizeof(uint32_t), unpredictable_seconds, (double)acc);

    free(predictable);
    free(unpredictable);
}

int main(void) {
    printf("experiment,variant,work_items,useful_bytes,seconds,mib_per_s,checksum\n");
    matrix_locality();
    stride_scan();
    branch_predictability();
    if (g_sink_double == -1.0 || g_sink_u64 == UINT64_MAX) return 99;
    return 0;
}
