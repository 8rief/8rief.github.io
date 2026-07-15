package com.example.tasktracker;

import com.example.tasktracker.domain.TaskPriority;
import com.example.tasktracker.domain.TaskStatus;
import com.example.tasktracker.service.TaskService;
import com.example.tasktracker.storage.JsonTaskStorage;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class TaskServiceTest {
    @TempDir
    Path tempDir;

    @Test
    void createsListsAndUpdatesTasks() {
        TaskService service = service(tempDir.resolve("tasks.json"));

        var created = service.create("  Write tests  ", TaskPriority.HIGH, List.of("Java", "api", "java"));
        var second = service.create("ship docs", null, null);
        var done = service.updateStatus(created.id(), TaskStatus.DONE);

        assertThat(done.status()).isEqualTo(TaskStatus.DONE);
        assertThat(service.list()).extracting("id").containsExactly(created.id(), second.id());
        assertThat(service.summary().total()).isEqualTo(2);
        assertThat(service.summary().done()).isEqualTo(1);
        assertThat(service.list().getFirst().title()).isEqualTo("Write tests");
        assertThat(service.list().getFirst().tags()).containsExactly("api", "java");
    }

    @Test
    void rejectsBlankTitle() {
        TaskService service = service(tempDir.resolve("tasks.json"));
        assertThatThrownBy(() -> service.create(" ", TaskPriority.LOW, List.of()))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("title");
    }

    private TaskService service(Path path) {
        return new TaskService(
                new JsonTaskStorage(path),
                Clock.fixed(Instant.parse("2026-06-25T09:00:00Z"), ZoneOffset.UTC)
        );
    }
}
