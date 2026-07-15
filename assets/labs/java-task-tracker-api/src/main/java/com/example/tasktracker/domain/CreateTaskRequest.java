package com.example.tasktracker.domain;

import jakarta.validation.constraints.NotBlank;

import java.util.Set;

public record CreateTaskRequest(
        @NotBlank(message = "title must not be blank") String title,
        TaskPriority priority,
        Set<String> tags
) {
}
