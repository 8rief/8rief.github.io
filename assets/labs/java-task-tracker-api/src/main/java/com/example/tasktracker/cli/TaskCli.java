package com.example.tasktracker.cli;

import com.example.tasktracker.domain.TaskItem;
import com.example.tasktracker.domain.TaskPriority;
import com.example.tasktracker.domain.TaskStatus;
import com.example.tasktracker.service.TaskService;
import com.example.tasktracker.storage.JsonTaskStorage;

import java.io.IOException;
import java.io.PrintStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;

public class TaskCli {
    private final TaskService service;

    public TaskCli(TaskService service) {
        this.service = service;
    }

    public static void main(String[] args) {
        int code = new TaskCli(defaultService()).run(args, System.out, System.err);
        if (code != 0) {
            System.exit(code);
        }
    }

    public int run(String[] args, PrintStream out, PrintStream err) {
        if (args.length == 0 || "help".equals(args[0])) {
            printHelp(out);
            return 0;
        }
        try {
            return switch (args[0]) {
                case "add" -> add(args, out);
                case "list" -> list(out);
                case "done" -> done(args, out);
                case "export-csv" -> exportCsv(args, out);
                default -> {
                    err.println("unknown command: " + args[0]);
                    printHelp(err);
                    yield 2;
                }
            };
        } catch (RuntimeException | IOException e) {
            err.println("error: " + e.getMessage());
            return 1;
        }
    }

    private int add(String[] args, PrintStream out) {
        if (args.length < 2) {
            throw new IllegalArgumentException("usage: add <title> [LOW|MEDIUM|HIGH]");
        }
        String title = args[1];
        TaskPriority priority = args.length >= 3 ? TaskPriority.valueOf(args[2].toUpperCase()) : TaskPriority.MEDIUM;
        TaskItem task = service.create(title, priority, List.of("cli"));
        out.printf("created id=%d status=%s priority=%s title=%s%n", task.id(), task.status(), task.priority(), task.title());
        return 0;
    }

    private int list(PrintStream out) {
        for (TaskItem task : service.list()) {
            out.printf("%d\t%s\t%s\t%s%n", task.id(), task.status(), task.priority(), task.title());
        }
        return 0;
    }

    private int done(String[] args, PrintStream out) {
        if (args.length != 2) {
            throw new IllegalArgumentException("usage: done <id>");
        }
        long id = Long.parseLong(args[1]);
        TaskItem task = service.updateStatus(id, TaskStatus.DONE);
        out.printf("updated id=%d status=%s%n", task.id(), task.status());
        return 0;
    }

    private int exportCsv(String[] args, PrintStream out) throws IOException {
        if (args.length != 2) {
            throw new IllegalArgumentException("usage: export-csv <path>");
        }
        Path output = Path.of(args[1]);
        Path parent = output.toAbsolutePath().getParent();
        if (parent != null) {
            Files.createDirectories(parent);
        }
        Files.writeString(output, service.toCsv());
        out.println("exported csv=" + output);
        return 0;
    }

    private static TaskService defaultService() {
        String configured = System.getProperty("task.tracker.data-file");
        if (configured == null || configured.isBlank()) {
            configured = System.getenv().getOrDefault("TASK_TRACKER_DATA_FILE", "reports/tasks-cli.json");
        }
        return new TaskService(new JsonTaskStorage(Path.of(configured)));
    }

    private static void printHelp(PrintStream stream) {
        stream.println("usage: TaskCli <command>");
        stream.println("commands: add <title> [LOW|MEDIUM|HIGH], list, done <id>, export-csv <path>");
    }
}
