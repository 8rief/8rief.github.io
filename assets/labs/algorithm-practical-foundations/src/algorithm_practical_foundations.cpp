#include <algorithm>
#include <cassert>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <optional>
#include <queue>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

using namespace std;

struct TestHarness {
    int passed = 0;

    template <class T, class U>
    void equal(const T& actual, const U& expected, const string& name) {
        if (!(actual == expected)) {
            ostringstream oss;
            oss << "FAILED: " << name;
            throw runtime_error(oss.str());
        }
        ++passed;
    }

    void truth(bool condition, const string& name) {
        if (!condition) {
            throw runtime_error("FAILED: " + name);
        }
        ++passed;
    }
};

template <class T>
string join_vector(const vector<T>& values, const string& sep = ",") {
    ostringstream oss;
    for (size_t i = 0; i < values.size(); ++i) {
        if (i) oss << sep;
        oss << values[i];
    }
    return oss.str();
}

string quote(const string& text) {
    string out = "\"";
    for (char c : text) {
        if (c == '\\' || c == '\"') out.push_back('\\');
        out.push_back(c);
    }
    out.push_back('\"');
    return out;
}

vector<int> top_k_largest(const vector<int>& values, int k) {
    if (k < 0) throw invalid_argument("k must be non-negative");
    priority_queue<int, vector<int>, greater<int>> heap;
    for (int value : values) {
        heap.push(value);
        if (static_cast<int>(heap.size()) > k) heap.pop();
    }
    vector<int> result;
    while (!heap.empty()) {
        result.push_back(heap.top());
        heap.pop();
    }
    sort(result.begin(), result.end(), greater<int>());
    return result;
}

vector<int> task_completion_order(const vector<pair<int, int>>& tasks) {
    // pair<priority, task_id>; higher priority runs first, then smaller id.
    priority_queue<pair<int, int>> pq;
    for (auto [priority, task_id] : tasks) {
        pq.push({priority, -task_id});
    }
    vector<int> order;
    while (!pq.empty()) {
        order.push_back(-pq.top().second);
        pq.pop();
    }
    return order;
}

map<string, int> word_frequency_ordered(const vector<string>& words) {
    unordered_map<string, int> counts;
    for (const string& word : words) ++counts[word];
    return map<string, int>(counts.begin(), counts.end());
}

optional<string> first_duplicate(const vector<string>& values) {
    unordered_set<string> seen;
    for (const string& value : values) {
        if (seen.count(value)) return value;
        seen.insert(value);
    }
    return nullopt;
}

optional<pair<int, int>> two_sum_indices(const vector<int>& values, int target) {
    unordered_map<int, int> first_index;
    for (int i = 0; i < static_cast<int>(values.size()); ++i) {
        int need = target - values[i];
        if (first_index.count(need)) return pair<int, int>{first_index[need], i};
        first_index.emplace(values[i], i);
    }
    return nullopt;
}

struct GridBfsResult {
    int distance = -1;
    vector<pair<int, int>> path;
};

GridBfsResult shortest_grid_path(const vector<string>& grid, pair<int, int> start, pair<int, int> goal) {
    const int rows = static_cast<int>(grid.size());
    const int cols = static_cast<int>(grid.at(0).size());
    vector<vector<int>> dist(rows, vector<int>(cols, -1));
    vector<vector<pair<int, int>>> parent(rows, vector<pair<int, int>>(cols, {-1, -1}));
    queue<pair<int, int>> q;
    auto inside = [&](int r, int c) { return 0 <= r && r < rows && 0 <= c && c < cols; };
    dist[start.first][start.second] = 0;
    q.push(start);
    const vector<pair<int, int>> dirs{{1,0},{-1,0},{0,1},{0,-1}};
    while (!q.empty()) {
        auto [r, c] = q.front();
        q.pop();
        if (pair<int, int>{r, c} == goal) break;
        for (auto [dr, dc] : dirs) {
            int nr = r + dr, nc = c + dc;
            if (!inside(nr, nc) || grid[nr][nc] == '#' || dist[nr][nc] != -1) continue;
            dist[nr][nc] = dist[r][c] + 1;
            parent[nr][nc] = {r, c};
            q.push({nr, nc});
        }
    }
    GridBfsResult result;
    result.distance = dist[goal.first][goal.second];
    if (result.distance == -1) return result;
    for (pair<int, int> cur = goal; cur.first != -1; cur = parent[cur.first][cur.second]) {
        result.path.push_back(cur);
        if (cur == start) break;
    }
    reverse(result.path.begin(), result.path.end());
    return result;
}

void dfs_component(int node, const vector<vector<int>>& graph, vector<int>& visited, vector<int>& component) {
    visited[node] = 1;
    component.push_back(node);
    for (int next : graph[node]) {
        if (!visited[next]) dfs_component(next, graph, visited, component);
    }
}

vector<vector<int>> connected_components(vector<vector<int>> graph) {
    for (auto& neighbors : graph) sort(neighbors.begin(), neighbors.end());
    vector<int> visited(graph.size(), 0);
    vector<vector<int>> components;
    for (int node = 0; node < static_cast<int>(graph.size()); ++node) {
        if (visited[node]) continue;
        vector<int> component;
        dfs_component(node, graph, visited, component);
        components.push_back(component);
    }
    return components;
}

void backtrack_subsets(const vector<int>& values, int index, vector<int>& current, vector<vector<int>>& out) {
    if (index == static_cast<int>(values.size())) {
        out.push_back(current);
        return;
    }
    backtrack_subsets(values, index + 1, current, out);
    current.push_back(values[index]);
    backtrack_subsets(values, index + 1, current, out);
    current.pop_back();
}

vector<vector<int>> all_subsets(vector<int> values) {
    vector<int> current;
    vector<vector<int>> out;
    backtrack_subsets(values, 0, current, out);
    return out;
}

int min_coins(const vector<int>& coins, int amount) {
    const int inf = numeric_limits<int>::max() / 4;
    vector<int> dp(amount + 1, inf);
    dp[0] = 0;
    for (int x = 1; x <= amount; ++x) {
        for (int coin : coins) {
            if (x >= coin) dp[x] = min(dp[x], dp[x - coin] + 1);
        }
    }
    return dp[amount] >= inf ? -1 : dp[amount];
}

int knapsack_01(const vector<int>& weights, const vector<int>& values, int capacity) {
    vector<int> dp(capacity + 1, 0);
    for (size_t i = 0; i < weights.size(); ++i) {
        for (int cap = capacity; cap >= weights[i]; --cap) {
            dp[cap] = max(dp[cap], dp[cap - weights[i]] + values[i]);
        }
    }
    return dp[capacity];
}

int grid_path_count_with_obstacles(const vector<string>& grid) {
    int rows = static_cast<int>(grid.size());
    int cols = static_cast<int>(grid.at(0).size());
    vector<vector<int>> dp(rows, vector<int>(cols, 0));
    if (grid[0][0] == '#') return 0;
    dp[0][0] = 1;
    for (int r = 0; r < rows; ++r) {
        for (int c = 0; c < cols; ++c) {
            if (grid[r][c] == '#') {
                dp[r][c] = 0;
                continue;
            }
            if (r) dp[r][c] += dp[r - 1][c];
            if (c) dp[r][c] += dp[r][c - 1];
        }
    }
    return dp[rows - 1][cols - 1];
}

struct BipartiteResult {
    bool ok = true;
    vector<int> color;
    pair<int, int> conflict{-1, -1};
};

BipartiteResult color_bipartite(const vector<vector<int>>& graph) {
    BipartiteResult result;
    result.color.assign(graph.size(), -1);
    for (int start = 0; start < static_cast<int>(graph.size()); ++start) {
        if (result.color[start] != -1) continue;
        queue<int> q;
        result.color[start] = 0;
        q.push(start);
        while (!q.empty()) {
            int node = q.front();
            q.pop();
            for (int next : graph[node]) {
                if (result.color[next] == -1) {
                    result.color[next] = result.color[node] ^ 1;
                    q.push(next);
                } else if (result.color[next] == result.color[node]) {
                    result.ok = false;
                    result.conflict = {node, next};
                    return result;
                }
            }
        }
    }
    return result;
}

struct ShortestPathResult {
    vector<int> dist;
    vector<int> parent;
    vector<int> path;
};

ShortestPathResult dijkstra_restore_path(int n, const vector<vector<pair<int, int>>>& graph, int source, int target) {
    const int inf = numeric_limits<int>::max() / 4;
    vector<int> dist(n, inf), parent(n, -1);
    priority_queue<pair<int, int>, vector<pair<int, int>>, greater<pair<int, int>>> pq;
    dist[source] = 0;
    pq.push({0, source});
    while (!pq.empty()) {
        auto [d, node] = pq.top();
        pq.pop();
        if (d != dist[node]) continue;
        for (auto [next, weight] : graph[node]) {
            if (dist[next] > d + weight) {
                dist[next] = d + weight;
                parent[next] = node;
                pq.push({dist[next], next});
            }
        }
    }
    vector<int> path;
    if (dist[target] < inf) {
        for (int cur = target; cur != -1; cur = parent[cur]) path.push_back(cur);
        reverse(path.begin(), path.end());
    }
    return {dist, parent, path};
}

long long pair_count(long long n) {
    return n * (n - 1) / 2;
}

long long adjacency_matrix_bytes(long long n) {
    return n * n * static_cast<long long>(sizeof(bool));
}

vector<pair<int, int>> brute_force_pairs_with_sum(const vector<int>& values, int target) {
    vector<pair<int, int>> pairs;
    for (int i = 0; i < static_cast<int>(values.size()); ++i) {
        for (int j = i + 1; j < static_cast<int>(values.size()); ++j) {
            if (values[i] + values[j] == target) pairs.push_back({i, j});
        }
    }
    return pairs;
}

bool hash_two_sum_matches_bruteforce(const vector<int>& values, int target) {
    bool brute_has = !brute_force_pairs_with_sum(values, target).empty();
    bool hash_has = two_sum_indices(values, target).has_value();
    return brute_has == hash_has;
}

int main() {
    TestHarness test;
    map<string, string> summary;

    vector<int> top3 = top_k_largest({4, 1, 7, 7, 3, 9, 2, 8}, 3);
    test.equal(top3, vector<int>({9, 8, 7}), "top_k_largest keeps largest three values");
    test.equal(top_k_largest({1, 2}, 0), vector<int>({}), "top_k_largest handles k zero");
    test.equal(task_completion_order({{2, 10}, {5, 11}, {5, 3}, {1, 7}}), vector<int>({3, 11, 10, 7}), "priority queue task order");
    summary["heap_top3"] = join_vector(top3);

    auto freq = word_frequency_ordered({"api", "db", "api", "cache", "db", "api"});
    test.equal(freq.at("api"), 3, "hash frequency count for api");
    test.equal(freq.at("db"), 2, "hash frequency count for db");
    test.equal(first_duplicate({"api", "db", "cache", "api"}).value(), string("api"), "first duplicate lookup");
    test.equal(two_sum_indices({2, 7, 11, 15}, 9).value(), pair<int, int>({0, 1}), "two sum indices");
    summary["hash_first_duplicate"] = "api";

    vector<string> grid = {
        "S..#.",
        ".#.#.",
        ".#...",
        ".###.",
        "....G"
    };
    GridBfsResult bfs = shortest_grid_path(grid, {0, 0}, {4, 4});
    test.equal(bfs.distance, 8, "BFS grid distance");
    test.equal(static_cast<int>(bfs.path.size()), 9, "BFS path has distance plus one nodes");
    test.equal(bfs.path.front(), pair<int, int>({0, 0}), "BFS path starts at source");
    test.equal(bfs.path.back(), pair<int, int>({4, 4}), "BFS path ends at goal");
    summary["bfs_distance"] = to_string(bfs.distance);

    vector<vector<int>> graph = {{1}, {0, 2}, {1}, {4}, {3}, {}};
    auto comps = connected_components(graph);
    test.equal(static_cast<int>(comps.size()), 3, "DFS components count");
    test.equal(comps[0], vector<int>({0, 1, 2}), "DFS first component");
    test.equal(comps[1], vector<int>({3, 4}), "DFS second component");
    test.equal(static_cast<int>(all_subsets({1, 2, 3}).size()), 8, "backtracking subset count");
    summary["dfs_components"] = to_string(comps.size());

    test.equal(min_coins({1, 3, 4}, 6), 2, "min coins for 6 uses 3+3");
    test.equal(min_coins({5, 7}, 1), -1, "min coins unreachable amount");
    test.equal(knapsack_01({2, 3, 4}, {4, 5, 6}, 5), 9, "0/1 knapsack capacity 5");
    test.equal(grid_path_count_with_obstacles({"...", ".#.", "..."}), 2, "grid path count with one obstacle");
    summary["dp_min_coins_6"] = "2";

    vector<vector<int>> bip = {{1, 3}, {0, 2}, {1, 3}, {0, 2}};
    auto bip_ok = color_bipartite(bip);
    test.truth(bip_ok.ok, "even cycle is bipartite");
    test.equal(static_cast<int>(set<int>(bip_ok.color.begin(), bip_ok.color.end()).size()), 2, "bipartite uses two colors");
    vector<vector<int>> triangle = {{1, 2}, {0, 2}, {0, 1}};
    auto bip_bad = color_bipartite(triangle);
    test.truth(!bip_bad.ok, "triangle is not bipartite");
    test.truth(bip_bad.conflict.first != -1, "bipartite conflict edge recorded");
    summary["bipartite_triangle_ok"] = bip_bad.ok ? "true" : "false";

    vector<vector<pair<int, int>>> weighted(5);
    auto add_edge = [&](int u, int v, int w) {
        weighted[u].push_back({v, w});
        weighted[v].push_back({u, w});
    };
    add_edge(0, 1, 2);
    add_edge(0, 2, 5);
    add_edge(1, 2, 1);
    add_edge(1, 3, 2);
    add_edge(2, 3, 1);
    add_edge(3, 4, 2);
    ShortestPathResult sp = dijkstra_restore_path(5, weighted, 0, 4);
    test.equal(sp.dist[4], 6, "Dijkstra target distance");
    test.equal(sp.path, vector<int>({0, 1, 3, 4}), "Dijkstra restored path");
    test.equal(sp.parent[4], 3, "Dijkstra predecessor for target");
    summary["dijkstra_distance_0_4"] = to_string(sp.dist[4]);
    summary["dijkstra_path_0_4"] = join_vector(sp.path, "->");

    test.equal(pair_count(100000), 4999950000LL, "pair count for n=100000");
    test.truth(adjacency_matrix_bytes(20000) >= 400000000LL, "adjacency matrix memory estimate");
    test.truth(hash_two_sum_matches_bruteforce({-3, 1, 4, 8, 11}, 5), "hash two-sum matches brute force positive case");
    test.truth(hash_two_sum_matches_bruteforce({1, 2, 4, 8}, 20), "hash two-sum matches brute force negative case");
    summary["pair_count_100000"] = to_string(pair_count(100000));

    std::filesystem::create_directories("reports");
    ofstream json("reports/results.json");
    json << "{\n";
    json << "  \"tests_passed\": " << test.passed << ",\n";
    int index = 0;
    for (auto it = summary.begin(); it != summary.end(); ++it, ++index) {
        json << "  \"" << it->first << "\": " << quote(it->second);
        json << (index + 1 == static_cast<int>(summary.size()) ? "\n" : ",\n");
    }
    json << "}\n";

    ofstream report("reports/algorithm_report.md");
    report << "# Algorithm Practical Foundations Lab Report\n\n";
    report << "- tests passed: " << test.passed << "\n";
    report << "- heap top3: " << summary["heap_top3"] << "\n";
    report << "- first duplicate: " << summary["hash_first_duplicate"] << "\n";
    report << "- BFS distance: " << summary["bfs_distance"] << "\n";
    report << "- DFS components: " << summary["dfs_components"] << "\n";
    report << "- DP min coins for 6: " << summary["dp_min_coins_6"] << "\n";
    report << "- triangle bipartite: " << summary["bipartite_triangle_ok"] << "\n";
    report << "- Dijkstra distance 0->4: " << summary["dijkstra_distance_0_4"] << "\n";
    report << "- Dijkstra path 0->4: " << summary["dijkstra_path_0_4"] << "\n";
    report << "- pair count for n=100000: " << summary["pair_count_100000"] << "\n";

    cout << "tests_passed=" << test.passed << "\n";
    cout << "heap_top3=" << summary["heap_top3"] << "\n";
    cout << "hash_first_duplicate=" << summary["hash_first_duplicate"] << "\n";
    cout << "bfs_distance=" << summary["bfs_distance"] << " path_nodes=" << bfs.path.size() << "\n";
    cout << "dfs_components=" << summary["dfs_components"] << " subset_count=8\n";
    cout << "dp_min_coins_6=" << summary["dp_min_coins_6"] << " knapsack_capacity_5=9\n";
    cout << "bipartite_square=true triangle=false\n";
    cout << "dijkstra_distance_0_4=" << summary["dijkstra_distance_0_4"] << " path=" << summary["dijkstra_path_0_4"] << "\n";
    cout << "pair_count_100000=" << summary["pair_count_100000"] << "\n";
    cout << "report=reports/algorithm_report.md\n";
    cout << "json=reports/results.json\n";
    return 0;
}
