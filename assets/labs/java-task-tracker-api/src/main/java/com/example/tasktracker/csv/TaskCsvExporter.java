package com.example.tasktracker.csv;

import com.example.tasktracker.domain.TaskItem;

import java.util.Collection;
import java.util.stream.Collectors;

public final class TaskCsvExporter {
    private TaskCsvExporter() {
    }

    public static String toCsv(Collection<TaskItem> tasks) {
        StringBuilder builder = new StringBuilder("id,title,status,priority,tags,createdAt\n");
        for (TaskItem task : tasks) {
            builder.append(task.id()).append(',')
                    .append(escape(task.title())).append(',')
                    .append(task.status()).append(',')
                    .append(task.priority()).append(',')
                    .append(escape(String.join(";", task.tags()))).append(',')
                    .append(task.createdAt()).append('\n');
        }
        return builder.toString();
    }

    private static String escape(String value) {
        if (value == null) {
            return "";
        }
        boolean needsQuotes = value.contains(",") || value.contains("\"") || value.contains("\n");
        String escaped = value.replace("\"", "\"\"");
        return needsQuotes ? "\"" + escaped + "\"" : escaped;
    }
}
