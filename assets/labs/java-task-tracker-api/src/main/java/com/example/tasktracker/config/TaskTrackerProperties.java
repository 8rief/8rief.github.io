package com.example.tasktracker.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.nio.file.Path;

@ConfigurationProperties(prefix = "task-tracker")
public record TaskTrackerProperties(Path dataFile) {
    public TaskTrackerProperties {
        if (dataFile == null) {
            dataFile = Path.of("reports/tasks-api.json");
        }
    }
}
