package com.example.tasktracker.service;

import com.example.tasktracker.csv.TaskCsvExporter;
import com.example.tasktracker.domain.TaskItem;
import com.example.tasktracker.domain.TaskPriority;
import com.example.tasktracker.domain.TaskStatus;
import com.example.tasktracker.domain.TaskSummary;
import com.example.tasktracker.storage.JsonTaskStorage;

import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.TreeSet;

public class TaskService {
    private final JsonTaskStorage storage;
    private final Clock clock;
    private final Map<Long, TaskItem> tasksById = new LinkedHashMap<>();
    private long nextId = 1;

    public TaskService(JsonTaskStorage storage) {
        this(storage, Clock.systemUTC());
    }

    public TaskService(JsonTaskStorage storage, Clock clock) {
        this.storage = storage;
        this.clock = clock;
        for (TaskItem task : storage.load()) {
            tasksById.put(task.id(), task);
            nextId = Math.max(nextId, task.id() + 1);
        }
    }

    public synchronized TaskItem create(String title, TaskPriority priority, Collection<String> tags) {
        String normalizedTitle = normalizeTitle(title);
        TaskPriority normalizedPriority = Optional.ofNullable(priority).orElse(TaskPriority.MEDIUM);
        Set<String> normalizedTags = normalizeTags(tags);
        TaskItem task = new TaskItem(
                nextId++,
                normalizedTitle,
                TaskStatus.OPEN,
                normalizedPriority,
                normalizedTags,
                Instant.now(clock)
        );
        tasksById.put(task.id(), task);
        persist();
        return task;
    }

    public synchronized List<TaskItem> list() {
        return tasksById.values().stream()
                .sorted(Comparator.comparingLong(TaskItem::id))
                .toList();
    }

    public synchronized TaskItem get(long id) {
        TaskItem task = tasksById.get(id);
        if (task == null) {
            throw new TaskNotFoundException(id);
        }
        return task;
    }

    public synchronized TaskItem updateStatus(long id, TaskStatus status) {
        if (status == null) {
            throw new IllegalArgumentException("status is required");
        }
        TaskItem updated = get(id).withStatus(status);
        tasksById.put(id, updated);
        persist();
        return updated;
    }

    public synchronized TaskSummary summary() {
        long open = count(TaskStatus.OPEN);
        long inProgress = count(TaskStatus.IN_PROGRESS);
        long done = count(TaskStatus.DONE);
        return new TaskSummary(tasksById.size(), open, inProgress, done);
    }

    public synchronized String toCsv() {
        return TaskCsvExporter.toCsv(list());
    }

    private long count(TaskStatus status) {
        return tasksById.values().stream().filter(task -> task.status() == status).count();
    }

    private void persist() {
        storage.save(new ArrayList<>(list()));
    }

    private static String normalizeTitle(String title) {
        if (title == null || title.trim().isEmpty()) {
            throw new IllegalArgumentException("title must not be blank");
        }
        return title.trim();
    }

    private static Set<String> normalizeTags(Collection<String> tags) {
        TreeSet<String> normalized = new TreeSet<>();
        if (tags == null) {
            return normalized;
        }
        for (String tag : tags) {
            if (tag != null && !tag.trim().isEmpty()) {
                normalized.add(tag.trim().toLowerCase());
            }
        }
        return normalized;
    }
}
