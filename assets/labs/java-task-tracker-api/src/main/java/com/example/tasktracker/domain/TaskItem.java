package com.example.tasktracker.domain;

import java.time.Instant;
import java.util.Set;

public record TaskItem(
        long id,
        String title,
        TaskStatus status,
        TaskPriority priority,
        Set<String> tags,
        Instant createdAt
) {
    public TaskItem withStatus(TaskStatus newStatus) {
        return new TaskItem(id, title, newStatus, priority, tags, createdAt);
    }
}
