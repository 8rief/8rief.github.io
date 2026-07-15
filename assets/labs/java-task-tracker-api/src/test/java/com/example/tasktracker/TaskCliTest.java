package com.example.tasktracker;

import com.example.tasktracker.cli.TaskCli;
import com.example.tasktracker.service.TaskService;
import com.example.tasktracker.storage.JsonTaskStorage;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;

import static org.assertj.core.api.Assertions.assertThat;

class TaskCliTest {
    @TempDir
    Path tempDir;

    @Test
    void cliCanAddListFinishAndExport() {
        TaskCli cli = new TaskCli(new TaskService(new JsonTaskStorage(tempDir.resolve("tasks.json"))));
        ByteArrayOutputStream stdout = new ByteArrayOutputStream();
        ByteArrayOutputStream stderr = new ByteArrayOutputStream();
        PrintStream out = new PrintStream(stdout, true, StandardCharsets.UTF_8);
        PrintStream err = new PrintStream(stderr, true, StandardCharsets.UTF_8);

        assertThat(cli.run(new String[]{"add", "write-tests", "HIGH"}, out, err)).isZero();
        assertThat(cli.run(new String[]{"list"}, out, err)).isZero();
        assertThat(cli.run(new String[]{"done", "1"}, out, err)).isZero();
        assertThat(cli.run(new String[]{"export-csv", tempDir.resolve("tasks.csv").toString()}, out, err)).isZero();

        String output = stdout.toString(StandardCharsets.UTF_8);
        assertThat(output).contains("created id=1");
        assertThat(output).contains("1\tOPEN\tHIGH\twrite-tests");
        assertThat(output).contains("updated id=1 status=DONE");
        assertThat(tempDir.resolve("tasks.csv")).content().contains("id,title,status,priority,tags,createdAt");
        assertThat(stderr.toString(StandardCharsets.UTF_8)).isEmpty();
    }
}
