package com.example.tasktracker;

import com.example.tasktracker.domain.TaskItem;
import com.example.tasktracker.domain.TaskPriority;
import com.example.tasktracker.domain.TaskStatus;
import com.example.tasktracker.storage.JsonTaskStorage;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;

class JsonTaskStorageTest {
    @TempDir
    Path tempDir;

    @Test
    void roundTripsTasksAsJson() {
        Path dataFile = tempDir.resolve("nested/tasks.json");
        JsonTaskStorage storage = new JsonTaskStorage(dataFile);
        TaskItem task = new TaskItem(1, "write README", TaskStatus.OPEN, TaskPriority.MEDIUM, Set.of("docs"), Instant.parse("2026-06-25T09:00:00Z"));

        storage.save(List.of(task));

        assertThat(storage.load()).containsExactly(task);
        assertThat(dataFile).exists();
    }
}
