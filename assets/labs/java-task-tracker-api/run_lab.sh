#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
mkdir -p reports .tools
TRANSCRIPT="$ROOT/reports/transcript.txt"
JDK_URL="https://api.adoptium.net/v3/binary/latest/21/ga/linux/x64/jdk/hotspot/normal/eclipse"
MAVEN_VERSION="3.9.10"
MAVEN_URL="https://archive.apache.org/dist/maven/maven-3/${MAVEN_VERSION}/binaries/apache-maven-${MAVEN_VERSION}-bin.tar.gz"

setup_java() {
  if command -v javac >/dev/null 2>&1; then
    return
  fi
  if [ ! -x .tools/jdk/bin/javac ]; then
    rm -rf .tools/jdk .tools/jdk-download
    mkdir -p .tools/jdk-download
    curl -L --fail --retry 3 -o .tools/jdk.tar.gz "$JDK_URL"
    tar -xzf .tools/jdk.tar.gz -C .tools/jdk-download --strip-components=1
    mv .tools/jdk-download .tools/jdk
  fi
  export JAVA_HOME="$ROOT/.tools/jdk"
  export PATH="$JAVA_HOME/bin:$PATH"
}

setup_maven() {
  if command -v mvn >/dev/null 2>&1; then
    return
  fi
  if [ ! -x .tools/maven/bin/mvn ]; then
    rm -rf .tools/maven .tools/maven-download
    mkdir -p .tools/maven-download
    curl -L --fail --retry 3 -o .tools/maven.tar.gz "$MAVEN_URL"
    tar -xzf .tools/maven.tar.gz -C .tools/maven-download --strip-components=1
    mv .tools/maven-download .tools/maven
  fi
  export PATH="$ROOT/.tools/maven/bin:$PATH"
}

{
  echo "# Java Task Tracker API lab transcript"
  date '+timestamp=%Y-%m-%d %H:%M:%S %z'
  echo "root=$ROOT"
  setup_java
  setup_maven
  java -version
  javac -version
  mvn -version | head -4
  rm -f reports/tasks-cli.json reports/tasks-api.json reports/tasks-cli.csv reports/api-server.log
  mvn -q test
  mvn -q -DskipTests package
  export TASK_TRACKER_DATA_FILE="$ROOT/reports/tasks-cli.json"
  mvn -q -DskipTests exec:java -Dexec.mainClass=com.example.tasktracker.cli.TaskCli -Dexec.args="add write-tests HIGH"
  mvn -q -DskipTests exec:java -Dexec.mainClass=com.example.tasktracker.cli.TaskCli -Dexec.args="add ship-docs MEDIUM"
  mvn -q -DskipTests exec:java -Dexec.mainClass=com.example.tasktracker.cli.TaskCli -Dexec.args="list"
  mvn -q -DskipTests exec:java -Dexec.mainClass=com.example.tasktracker.cli.TaskCli -Dexec.args="done 1"
  mvn -q -DskipTests exec:java -Dexec.mainClass=com.example.tasktracker.cli.TaskCli -Dexec.args="export-csv reports/tasks-cli.csv"
  echo "--- CLI CSV excerpt ---"
  sed -n '1,4p' reports/tasks-cli.csv
  echo "--- API smoke ---"
  java -jar target/task-tracker-0.1.0.jar --server.address=127.0.0.1 --server.port=18180 --task-tracker.data-file=reports/tasks-api.json > reports/api-server.log 2>&1 &
  server_pid=$!
  trap 'kill "$server_pid" 2>/dev/null || true' EXIT
  for _ in $(seq 1 60); do
    if curl -s --fail http://127.0.0.1:18180/api/tasks/summary >/tmp/task-summary.json; then
      break
    fi
    sleep 1
  done
  curl -s --fail -H 'Content-Type: application/json' -d '{"title":"write README","priority":"HIGH","tags":["docs","java"]}' http://127.0.0.1:18180/api/tasks | python3 -m json.tool
  curl -s --fail http://127.0.0.1:18180/api/tasks/summary | python3 -m json.tool
  curl -s --fail -X PATCH -H 'Content-Type: application/json' -d '{"status":"DONE"}' http://127.0.0.1:18180/api/tasks/1/status | python3 -m json.tool
  curl -s --fail http://127.0.0.1:18180/api/tasks/export.csv | sed -n '1,4p'
  kill "$server_pid"
  trap - EXIT
} 2>&1 | tee "$TRANSCRIPT"
