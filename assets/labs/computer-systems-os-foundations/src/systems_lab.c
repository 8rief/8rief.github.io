#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <pthread.h>
#include <signal.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static int global_value = 17;
static volatile long controlled_shared = 0;
static pthread_mutex_t barrier_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t barrier_cond = PTHREAD_COND_INITIALIZER;
static int barrier_readers = 0;
static long mutex_counter = 0;
static pthread_mutex_t counter_mutex = PTHREAD_MUTEX_INITIALIZER;
static volatile long long cache_sink = 0;
static volatile sig_atomic_t got_usr1 = 0;

static void die(const char *message) {
    perror(message);
    exit(1);
}

static uint64_t now_ns(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) {
        die("clock_gettime");
    }
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

static void demo_data(void) {
    uint32_t value = 0x12345678U;
    unsigned char *bytes = (unsigned char *)&value;
    bool little = bytes[0] == 0x78U;
    int32_t negative_one = -1;
    printf("data_uint32_decimal=%" PRIu32 "\n", value);
    printf("data_byte0_hex=%02x\n", bytes[0]);
    printf("data_little_endian=%s\n", little ? "true" : "false");
    printf("data_signed_minus_one_as_uint32=%" PRIu32 "\n", (uint32_t)negative_one);
    printf("data_uint32_size=%zu\n", sizeof(uint32_t));
}

static void demo_memory(void) {
    int stack_value = 23;
    int *heap_value = malloc(sizeof(*heap_value));
    if (heap_value == NULL) {
        die("malloc");
    }
    *heap_value = 29;
    uintptr_t stack_addr = (uintptr_t)&stack_value;
    uintptr_t heap_addr = (uintptr_t)heap_value;
    uintptr_t global_addr = (uintptr_t)&global_value;
    printf("memory_stack_value=%d\n", stack_value);
    printf("memory_heap_value=%d\n", *heap_value);
    printf("memory_global_value=%d\n", global_value);
    printf("memory_stack_heap_distinct=%s\n", stack_addr != heap_addr ? "true" : "false");
    printf("memory_stack_global_distinct=%s\n", stack_addr != global_addr ? "true" : "false");
    printf("memory_heap_global_distinct=%s\n", heap_addr != global_addr ? "true" : "false");
    free(heap_value);
}

static void demo_process(void) {
    pid_t child = fork();
    if (child < 0) {
        die("fork");
    }
    if (child == 0) {
        _exit(42);
    }
    int status = 0;
    if (waitpid(child, &status, 0) < 0) {
        die("waitpid");
    }
    int exit_code = WIFEXITED(status) ? WEXITSTATUS(status) : -1;
    printf("process_parent_pid_positive=%s\n", getpid() > 0 ? "true" : "false");
    printf("process_child_pid_positive=%s\n", child > 0 ? "true" : "false");
    printf("process_child_exit_code=%d\n", exit_code);
}

static void demo_fd_fs(void) {
    const char *path = ".lab_tmp/fd-demo.txt";
    int fd = open(path, O_CREAT | O_TRUNC | O_RDWR, 0644);
    if (fd < 0) {
        die("open fd-demo");
    }
    const char *payload = "systems\n";
    ssize_t written = write(fd, payload, strlen(payload));
    if (written < 0) {
        die("write fd-demo");
    }
    if (lseek(fd, 0, SEEK_SET) < 0) {
        die("lseek fd-demo");
    }
    char buffer[32] = {0};
    ssize_t read_bytes = read(fd, buffer, sizeof(buffer) - 1);
    if (read_bytes < 0) {
        die("read fd-demo");
    }
    struct stat st;
    if (fstat(fd, &st) != 0) {
        die("fstat fd-demo");
    }
    close(fd);

    int pipefd[2];
    if (pipe(pipefd) != 0) {
        die("pipe");
    }
    const char *pipe_payload = "pipe-ok";
    if (write(pipefd[1], pipe_payload, strlen(pipe_payload)) < 0) {
        die("write pipe");
    }
    close(pipefd[1]);
    char pipe_buffer[32] = {0};
    ssize_t pipe_read = read(pipefd[0], pipe_buffer, sizeof(pipe_buffer) - 1);
    if (pipe_read < 0) {
        die("read pipe");
    }
    close(pipefd[0]);

    printf("fd_file_bytes_written=%zd\n", written);
    printf("fd_file_bytes_read=%zd\n", read_bytes);
    printf("fd_file_inode_positive=%s\n", st.st_ino > 0 ? "true" : "false");
    printf("fd_pipe_bytes_read=%zd\n", pipe_read);
    printf("fd_pipe_message=%s\n", pipe_buffer);
}

static void demo_virtual_memory(void) {
    long page_size = sysconf(_SC_PAGESIZE);
    if (page_size <= 0) {
        die("sysconf page size");
    }
    int *page = mmap(NULL, (size_t)page_size, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (page == MAP_FAILED) {
        die("mmap page");
    }
    *page = 7;

    int pipefd[2];
    if (pipe(pipefd) != 0) {
        die("pipe cow");
    }
    pid_t child = fork();
    if (child < 0) {
        die("fork cow");
    }
    if (child == 0) {
        close(pipefd[0]);
        *page = 99;
        char msg[32];
        int len = snprintf(msg, sizeof(msg), "%d", *page);
        if (write(pipefd[1], msg, (size_t)len) < 0) {
            _exit(2);
        }
        close(pipefd[1]);
        _exit(0);
    }
    close(pipefd[1]);
    char child_value[32] = {0};
    ssize_t n = read(pipefd[0], child_value, sizeof(child_value) - 1);
    if (n < 0) {
        die("read cow");
    }
    close(pipefd[0]);
    int status = 0;
    if (waitpid(child, &status, 0) < 0) {
        die("waitpid cow");
    }
    printf("vm_page_size=%ld\n", page_size);
    printf("vm_mmap_initial_value=7\n");
    printf("vm_cow_child_value=%s\n", child_value);
    printf("vm_cow_parent_value=%d\n", *page);
    printf("vm_cow_parent_unchanged=%s\n", *page == 7 ? "true" : "false");
    if (munmap(page, (size_t)page_size) != 0) {
        die("munmap page");
    }
}

static void *controlled_race_thread(void *arg) {
    (void)arg;
    long local = controlled_shared;
    if (pthread_mutex_lock(&barrier_mutex) != 0) {
        abort();
    }
    barrier_readers += 1;
    if (barrier_readers == 2) {
        pthread_cond_broadcast(&barrier_cond);
    } else {
        while (barrier_readers < 2) {
            pthread_cond_wait(&barrier_cond, &barrier_mutex);
        }
    }
    if (pthread_mutex_unlock(&barrier_mutex) != 0) {
        abort();
    }
    controlled_shared = local + 1;
    return NULL;
}

static void *mutex_counter_thread(void *arg) {
    long iterations = *(long *)arg;
    for (long i = 0; i < iterations; i += 1) {
        if (pthread_mutex_lock(&counter_mutex) != 0) {
            abort();
        }
        mutex_counter += 1;
        if (pthread_mutex_unlock(&counter_mutex) != 0) {
            abort();
        }
    }
    return NULL;
}

static void demo_threads(void) {
    pthread_t r1, r2;
    if (pthread_create(&r1, NULL, controlled_race_thread, NULL) != 0) {
        die("pthread_create race 1");
    }
    if (pthread_create(&r2, NULL, controlled_race_thread, NULL) != 0) {
        die("pthread_create race 2");
    }
    pthread_join(r1, NULL);
    pthread_join(r2, NULL);

    const int workers = 4;
    long iterations = 50000;
    pthread_t threads[workers];
    for (int i = 0; i < workers; i += 1) {
        if (pthread_create(&threads[i], NULL, mutex_counter_thread, &iterations) != 0) {
            die("pthread_create mutex");
        }
    }
    for (int i = 0; i < workers; i += 1) {
        pthread_join(threads[i], NULL);
    }
    long expected = iterations * workers;
    printf("thread_controlled_race_expected=2\n");
    printf("thread_controlled_race_actual=%ld\n", controlled_shared);
    printf("thread_mutex_expected=%ld\n", expected);
    printf("thread_mutex_actual=%ld\n", mutex_counter);
    printf("thread_mutex_correct=%s\n", mutex_counter == expected ? "true" : "false");
}

static void usr1_handler(int signo) {
    (void)signo;
    got_usr1 = 1;
}

static void demo_signal_ipc(void) {
    int ready_pipe[2];
    int msg_pipe[2];
    if (pipe(ready_pipe) != 0 || pipe(msg_pipe) != 0) {
        die("pipe signal");
    }
    pid_t child = fork();
    if (child < 0) {
        die("fork signal");
    }
    if (child == 0) {
        close(ready_pipe[0]);
        close(msg_pipe[0]);
        struct sigaction action;
        memset(&action, 0, sizeof(action));
        action.sa_handler = usr1_handler;
        sigemptyset(&action.sa_mask);
        if (sigaction(SIGUSR1, &action, NULL) != 0) {
            _exit(3);
        }
        if (write(ready_pipe[1], "R", 1) < 0) {
            _exit(4);
        }
        close(ready_pipe[1]);
        while (!got_usr1) {
            pause();
        }
        if (write(msg_pipe[1], "signal-ok", 9) < 0) {
            _exit(5);
        }
        close(msg_pipe[1]);
        _exit(0);
    }
    close(ready_pipe[1]);
    close(msg_pipe[1]);
    char ready = 0;
    if (read(ready_pipe[0], &ready, 1) != 1) {
        die("read ready");
    }
    close(ready_pipe[0]);
    if (kill(child, SIGUSR1) != 0) {
        die("kill SIGUSR1");
    }
    char msg[32] = {0};
    ssize_t n = read(msg_pipe[0], msg, sizeof(msg) - 1);
    if (n < 0) {
        die("read signal msg");
    }
    close(msg_pipe[0]);
    int status = 0;
    if (waitpid(child, &status, 0) < 0) {
        die("waitpid signal");
    }
    printf("signal_ready_byte=%c\n", ready);
    printf("signal_ipc_message=%s\n", msg);
    printf("signal_child_exit_code=%d\n", WIFEXITED(status) ? WEXITSTATUS(status) : -1);
}

static void demo_cache_performance(void) {
    const int n = 1024;
    const int repeat = 6;
    size_t total = (size_t)n * (size_t)n;
    int *matrix = malloc(total * sizeof(*matrix));
    if (matrix == NULL) {
        die("malloc matrix");
    }
    for (size_t i = 0; i < total; i += 1) {
        matrix[i] = (int)(i & 255U);
    }
    long long row_sum = 0;
    uint64_t row_start = now_ns();
    for (int r = 0; r < repeat; r += 1) {
        for (int i = 0; i < n; i += 1) {
            for (int j = 0; j < n; j += 1) {
                row_sum += matrix[(size_t)i * (size_t)n + (size_t)j];
            }
        }
    }
    uint64_t row_ns = now_ns() - row_start;

    long long col_sum = 0;
    uint64_t col_start = now_ns();
    for (int r = 0; r < repeat; r += 1) {
        for (int j = 0; j < n; j += 1) {
            for (int i = 0; i < n; i += 1) {
                col_sum += matrix[(size_t)i * (size_t)n + (size_t)j];
            }
        }
    }
    uint64_t col_ns = now_ns() - col_start;
    cache_sink = row_sum + col_sum;
    double ratio = row_ns == 0 ? 0.0 : (double)col_ns / (double)row_ns;
    printf("cache_matrix_n=%d\n", n);
    printf("cache_row_major_ns=%" PRIu64 "\n", row_ns);
    printf("cache_column_major_ns=%" PRIu64 "\n", col_ns);
    printf("cache_column_to_row_ratio=%.3f\n", ratio);
    printf("cache_sums_equal=%s\n", row_sum == col_sum ? "true" : "false");
    free(matrix);
}

int main(void) {
    demo_data();
    demo_memory();
    demo_process();
    demo_fd_fs();
    demo_virtual_memory();
    demo_threads();
    demo_signal_ipc();
    demo_cache_performance();
    printf("systems_os_status=ok\n");
    return 0;
}
