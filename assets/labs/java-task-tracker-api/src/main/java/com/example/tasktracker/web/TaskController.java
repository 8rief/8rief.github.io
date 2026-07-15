package com.example.tasktracker.web;

import com.example.tasktracker.domain.CreateTaskRequest;
import com.example.tasktracker.domain.TaskItem;
import com.example.tasktracker.domain.TaskSummary;
import com.example.tasktracker.domain.UpdateStatusRequest;
import com.example.tasktracker.service.TaskService;
import jakarta.validation.Valid;
import org.springframework.http.MediaType;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@Validated
@RestController
@RequestMapping("/api/tasks")
public class TaskController {
    private final TaskService service;

    public TaskController(TaskService service) {
        this.service = service;
    }

    @GetMapping
    public List<TaskItem> list() {
        return service.list();
    }

    @GetMapping("/summary")
    public TaskSummary summary() {
        return service.summary();
    }

    @PostMapping
    public TaskItem create(@Valid @RequestBody CreateTaskRequest request) {
        return service.create(request.title(), request.priority(), request.tags());
    }

    @PatchMapping("/{id}/status")
    public TaskItem updateStatus(@PathVariable long id, @Valid @RequestBody UpdateStatusRequest request) {
        return service.updateStatus(id, request.status());
    }

    @GetMapping(value = "/export.csv", produces = "text/csv; charset=utf-8")
    public String exportCsv() {
        return service.toCsv();
    }
}
