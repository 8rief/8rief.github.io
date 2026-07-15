package com.example.tasktracker.storage;

import com.example.tasktracker.domain.TaskItem;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.Collection;
import java.util.List;

public final class JsonTaskStorage {
    private static final TypeReference<List<TaskItem>> TASK_LIST = new TypeReference<>() {
    };

    private final Path dataFile;
    private final ObjectMapper objectMapper;

    public JsonTaskStorage(Path dataFile) {
        this.dataFile = dataFile;
        this.objectMapper = new ObjectMapper().registerModule(new JavaTimeModule());
    }

    public Path dataFile() {
        return dataFile;
    }

    public List<TaskItem> load() {
        if (!Files.exists(dataFile)) {
            return List.of();
        }
        try {
            return objectMapper.readValue(dataFile.toFile(), TASK_LIST);
        } catch (IOException e) {
            throw new UncheckedIOException("failed to read task data file: " + dataFile, e);
        }
    }

    public void save(Collection<TaskItem> tasks) {
        try {
            Path parent = dataFile.toAbsolutePath().getParent();
            if (parent != null) {
                Files.createDirectories(parent);
            }
            Path temp = dataFile.resolveSibling(dataFile.getFileName() + ".tmp");
            objectMapper.writerWithDefaultPrettyPrinter().writeValue(temp.toFile(), tasks);
            moveAtomicallyWhenPossible(temp, dataFile);
        } catch (IOException e) {
            throw new UncheckedIOException("failed to write task data file: " + dataFile, e);
        }
    }

    private static void moveAtomicallyWhenPossible(Path source, Path target) throws IOException {
        try {
            Files.move(source, target, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
        } catch (AtomicMoveNotSupportedException ignored) {
            Files.move(source, target, StandardCopyOption.REPLACE_EXISTING);
        }
    }
}
