package com.example.tasktracker;

import com.example.tasktracker.config.TaskTrackerProperties;
import com.example.tasktracker.service.TaskService;
import com.example.tasktracker.storage.JsonTaskStorage;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
@EnableConfigurationProperties(TaskTrackerProperties.class)
public class TaskTrackerApplication {
    public static void main(String[] args) {
        SpringApplication.run(TaskTrackerApplication.class, args);
    }

    @Bean
    JsonTaskStorage jsonTaskStorage(TaskTrackerProperties properties) {
        return new JsonTaskStorage(properties.dataFile());
    }

    @Bean
    TaskService taskService(JsonTaskStorage storage) {
        return new TaskService(storage);
    }
}
