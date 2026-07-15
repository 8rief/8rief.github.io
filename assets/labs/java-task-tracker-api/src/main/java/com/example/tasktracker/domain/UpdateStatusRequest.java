package com.example.tasktracker.domain;

import jakarta.validation.constraints.NotNull;

public record UpdateStatusRequest(@NotNull(message = "status is required") TaskStatus status) {
}
