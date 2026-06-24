---
layout: post
title: "TypeScript 结构类型、narrowing 和判别联合：把数据形状变成可检查的分支"
date: 2026-06-24 15:20:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用结构类型、narrowing 和判别联合，把 JavaScript 对象形状和业务分支变成 TypeScript 可检查的约束。"
tags: [typescript, linux, type-system, narrowing, testing]
---
{% raw %}

> 主题：特色语言 / TypeScript / structural typing / narrowing / discriminated union  
> 本文命令已在 Ubuntu 24.04、Node.js v22.22.2、npm 10.9.7、TypeScript 6.0.3 环境下本地执行验证。实验覆盖 `npm install`、`npx tsc --version`、`npm run typecheck`、`npm test`、`npm start`，以及 2 个预期失败的类型检查样例。

Rust 文章讲 ownership，把资源流动交给编译器检查；Go 文章讲 goroutine 和 channel，把并发数据流放进标准工具链。TypeScript 值得放在这一组，是因为它解决的是另一类常见工程问题：JavaScript 代码经常要处理来自接口、配置、CLI 或页面事件的数据，这些数据一旦进入系统，就会沿着分支、回调和模块边界传播。只靠注释说明“这个对象应该长什么样”，很容易在新增字段、新增事件类型或重构分支时漏掉一处。

TypeScript 的核心价值是把“对象形状”和“分支条件”变成可检查的约束。结构类型说明一个值需要哪些字段；narrowing 根据条件把联合类型缩小到某个分支；判别联合用一个稳定字段连接业务分支和类型分支。本文用一个事件汇总例子，把这三件事连成一条可复现的验证流。

## 学习目标

读完并执行本文命令后，你应该能够：

1. 解释 TypeScript 的结构类型为什么看“形状”而不是看类名。
2. 用判别字段 `kind` 建模一组事件类型。
3. 在 `switch` 分支中依靠 narrowing 安全访问不同事件的字段。
4. 用 `assertNever` 建立新增事件时的穷尽检查。
5. 用 `tsc --noEmit`、`tsc -p`、简单 Node 测试和 compile-fail 样例建立最小验证流。

## 先修知识

建议先读：

- [Rust ownership、borrowing 和 Cargo：把资源流动交给编译器检查](/computer-science-teaching/2026/06/24/rust-ownership-borrowing-cargo.html)
- [Go goroutines、channels 和标准工具链：用通信组织并发](/computer-science-teaching/2026/06/24/go-goroutines-channels-toolchain.html)

需要知道：

- JavaScript 对象、数组、函数和 `switch` 的基本语法；
- 命令行下使用 Node/npm 的基本流程；
- “测试通过”和“类型检查通过”检查的是两类问题：前者运行代码，后者检查代码在所有声明路径上的形状关系。

## 核心模型：形状、缩小、穷尽

TypeScript Handbook 把 TypeScript 描述为 JavaScript 的带类型语法层。它的类型系统是结构类型系统：如果两个对象拥有所需的字段和字段类型，它们就可以兼容，即使它们不是同一个类创建的对象。这和 C++/Java 中常见的名义类型直觉不同。

本文使用事件汇总例子建立三层模型：

![TypeScript 结构类型和 narrowing 工作流](/assets/diagrams/typescript-structural-narrowing.svg)

1. **结构类型**：`Signup` 需要 `kind`、`userId`、`plan`。只要对象满足这个形状，它就可以作为 `Signup` 使用。
2. **判别联合**：`TrackingEvent = PageView | Signup | Purchase`，每个分支都有字面量字段 `kind`。
3. **narrowing**：`switch (event.kind)` 进入 `case "purchase"` 后，编译器知道 `event` 是 `Purchase`，于是允许访问 `amountCents`。
4. **穷尽检查**：默认分支把 `event` 传给 `assertNever()`。如果以后新增 `Refund` 却忘记处理，`event` 就不再是 `never`，类型检查会失败。

这条主线的重点是让“业务分支”和“类型分支”同步变化。新增事件时，不应该只靠搜索字符串找分支；编译器应该能指出漏掉的处理位置。

## 建立项目

创建目录并写 `package.json`：

```bash
mkdir -p typescript-structural-narrowing/{src/test,compile_fail,reports}
cd typescript-structural-narrowing
cat > package.json <<'JSON'
{
  "name": "typescript-structural-narrowing-lab",
  "version": "0.1.0",
  "private": true,
  "type": "commonjs",
  "scripts": {
    "typecheck": "tsc --noEmit",
    "build": "tsc -p tsconfig.json",
    "test": "npm run build --silent && node dist/test/events.test.js",
    "start": "npm run build --silent && node dist/index.js"
  },
  "devDependencies": {
    "typescript": "6.0.3"
  }
}
JSON
```

`typecheck` 和 `build` 分开是一个实用习惯：前者只检查类型，不写 `dist/`；后者生成 JavaScript，供测试和示例运行。

写 `tsconfig.json`：

```bash
cat > tsconfig.json <<'JSON'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "CommonJS",
    "rootDir": "src",
    "outDir": "dist",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": true,
    "lib": ["ES2022", "DOM"]
  },
  "include": ["src/**/*.ts"]
}
JSON
```

这里的关键不是选项数量，而是检查边界：`strict` 打开严格类型检查；`noUncheckedIndexedAccess` 让数组下标访问体现“可能没有元素”；`exactOptionalPropertyTypes` 避免把“属性不存在”和“属性值为 `undefined`”混成一个含义；`noFallthroughCasesInSwitch` 阻止 `switch` 分支意外贯穿。

## 建模事件类型

写 `src/events.ts`：

```bash
cat > src/events.ts <<'TS'
export type PageView = {
  kind: "page_view";
  path: string;
  seconds: number;
};

export type Signup = {
  kind: "signup";
  userId: string;
  plan: "free" | "pro";
};

export type Purchase = {
  kind: "purchase";
  orderId: string;
  amountCents: number;
};

export type TrackingEvent = PageView | Signup | Purchase;

export type Summary = {
  views: number;
  engagedSeconds: number;
  proSignups: number;
  revenueCents: number;
};

export function emptySummary(): Summary {
  return {
    views: 0,
    engagedSeconds: 0,
    proSignups: 0,
    revenueCents: 0,
  };
}

function assertNever(value: never): never {
  throw new Error(`unhandled event: ${JSON.stringify(value)}`);
}

export function applyEvent(summary: Summary, event: TrackingEvent): Summary {
  switch (event.kind) {
    case "page_view":
      return {
        ...summary,
        views: summary.views + 1,
        engagedSeconds: summary.engagedSeconds + event.seconds,
      };
    case "signup":
      return {
        ...summary,
        proSignups: summary.proSignups + (event.plan === "pro" ? 1 : 0),
      };
    case "purchase":
      return {
        ...summary,
        revenueCents: summary.revenueCents + event.amountCents,
      };
    default:
      return assertNever(event);
  }
}

export function summarize(events: readonly TrackingEvent[]): Summary {
  return events.reduce(applyEvent, emptySummary());
}

export function describeEvent(event: TrackingEvent): string {
  switch (event.kind) {
    case "page_view":
      return `page ${event.path} stayed ${event.seconds}s`;
    case "signup":
      return `signup ${event.userId} on ${event.plan}`;
    case "purchase":
      return `purchase ${event.orderId} for ${event.amountCents} cents`;
    default:
      return assertNever(event);
  }
}

export function isRevenueEvent(event: TrackingEvent): event is Purchase {
  return event.kind === "purchase";
}
TS
```

几个细节值得停下来解释。

`kind` 字段是类型分支的锚点。`TrackingEvent` 是三个对象类型的联合；没有 `kind` 时，编译器只能看到“可能是三种对象之一”。进入 `case "purchase"` 后，`event.kind` 的字面量值已经确定，编译器就能把 `event` 缩小成 `Purchase`。

`assertNever()` 是穷尽检查的关键。`never` 表示这里不应该再有任何可能值。当前三个分支都处理完后，默认分支里的 `event` 可以被推断为 `never`；如果给联合类型新增一个分支但忘了改 `switch`，这里就会收到“某个实际类型不能赋给 `never`”的错误。

`isRevenueEvent()` 返回值里的 `event is Purchase` 是 type predicate。它告诉编译器：当这个函数返回 `true` 时，传入的 `TrackingEvent` 可以缩小成 `Purchase`。这样 `filter(isRevenueEvent)` 之后得到的数组就能安全访问 `amountCents`。

## 写运行入口

写 `src/index.ts`：

```bash
cat > src/index.ts <<'TS'
import { describeEvent, isRevenueEvent, summarize, type TrackingEvent } from "./events";

const events: TrackingEvent[] = [
  { kind: "page_view", path: "/cpp-build-pipeline", seconds: 42 },
  { kind: "signup", userId: "u-001", plan: "pro" },
  { kind: "purchase", orderId: "o-100", amountCents: 3900 },
];

for (const event of events) {
  console.log(describeEvent(event));
}

const revenueEvents = events.filter(isRevenueEvent);
console.log(`revenue events=${revenueEvents.length}`);
console.log(JSON.stringify(summarize(events), null, 2));
TS
```

运行入口不承担复杂业务，只展示数据如何穿过类型系统。`events` 的数组类型是 `TrackingEvent[]`，所以每个对象都必须匹配三个事件分支之一。`revenueEvents` 的元素类型会被缩小成 `Purchase`，这就是 type predicate 的可见效果。

## 写最小测试

写 `src/test/events.test.ts`：

```bash
cat > src/test/events.test.ts <<'TS'
import { applyEvent, describeEvent, emptySummary, isRevenueEvent, summarize, type TrackingEvent } from "../events";

function assert(condition: unknown, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

function assertEqual<T>(actual: T, expected: T, message: string): void {
  if (actual !== expected) {
    throw new Error(`${message}: expected ${String(expected)}, got ${String(actual)}`);
  }
}

const eventFromAnotherModule = {
  kind: "signup",
  userId: "u-structural",
  plan: "pro",
} satisfies TrackingEvent;

const summary = summarize([
  { kind: "page_view", path: "/", seconds: 3 },
  eventFromAnotherModule,
  { kind: "purchase", orderId: "o-1", amountCents: 1200 },
]);

assertEqual(summary.views, 1, "page views");
assertEqual(summary.engagedSeconds, 3, "engaged seconds");
assertEqual(summary.proSignups, 1, "pro signups");
assertEqual(summary.revenueCents, 1200, "revenue cents");

const revenueOnly = ([
  { kind: "page_view", path: "/docs", seconds: 10 },
  { kind: "purchase", orderId: "o-2", amountCents: 800 },
] satisfies TrackingEvent[]).filter(isRevenueEvent);

assertEqual(revenueOnly.length, 1, "narrowed revenue count");
assertEqual(revenueOnly[0]!.amountCents, 800, "narrowed purchase amount");

const next = applyEvent(emptySummary(), { kind: "page_view", path: "/x", seconds: 8 });
assertEqual(next.views, 1, "applyEvent updates view count");
assert(describeEvent({ kind: "signup", userId: "u-2", plan: "free" }).includes("free"), "describe signup");

console.log("events.test.ts: all checks passed");
TS
```

这里用 Node 直接跑编译后的测试文件，没有引入测试框架。真实项目可以换成 Vitest、Jest 或 Node 自带测试模块，但本文的最小实验只需要确认：编译后的代码能运行，事件汇总结果正确，type predicate 之后能访问 `Purchase` 字段。

`satisfies TrackingEvent` 也值得注意。它检查对象是否满足目标类型，同时尽量保留对象自身更精确的字面量信息。相比直接写类型断言，`satisfies` 更适合表达“请帮我检查这个对象形状，不要粗暴地把它当成某个类型”。

## 建立 compile-fail 样例

第一个失败样例模拟新增事件但忘记改 `switch`。写 `compile_fail/missing_case.ts`：

```bash
cat > compile_fail/missing_case.ts <<'TS'
type PageView = { kind: "page_view"; path: string; seconds: number };
type Signup = { kind: "signup"; userId: string; plan: "free" | "pro" };
type Purchase = { kind: "purchase"; orderId: string; amountCents: number };
type Refund = { kind: "refund"; orderId: string; amountCents: number };

type Event = PageView | Signup | Purchase | Refund;

function assertNever(value: never): never {
  throw new Error(String(value));
}

export function label(event: Event): string {
  switch (event.kind) {
    case "page_view":
      return event.path;
    case "signup":
      return event.userId;
    case "purchase":
      return event.orderId;
    default:
      return assertNever(event);
  }
}
TS
```

第二个失败样例模拟把普通字符串塞进字面量联合。写 `compile_fail/wide_string.ts`：

```bash
cat > compile_fail/wide_string.ts <<'TS'
export {};

type Signup = { kind: "signup"; userId: string; plan: "free" | "pro" };

const planFromCli: string = "enterprise";

const event: Signup = {
  kind: "signup",
  userId: "u-wide",
  plan: planFromCli,
};

console.log(event);
TS
```

这两个例子都应该失败。失败本身不是坏事，它把原本可能进入运行时的错误提前到了类型检查阶段。

## 执行验证

安装依赖并查看 TypeScript 版本：

```bash
npm install
npx tsc --version
```

本地输出：

```text
Version 6.0.3
```

执行类型检查、测试和示例运行：

```bash
npm run typecheck --silent
npm test --silent
npm start --silent
```

本地测试输出：

```text
events.test.ts: all checks passed
```

示例输出：

```text
page /cpp-build-pipeline stayed 42s
signup u-001 on pro
purchase o-100 for 3900 cents
revenue events=1
{
  "views": 1,
  "engagedSeconds": 42,
  "proSignups": 1,
  "revenueCents": 3900
}
```

执行两个预期失败样例：

```bash
npx tsc --noEmit --ignoreConfig --strict --lib ES2022,DOM compile_fail/missing_case.ts
npx tsc --noEmit --ignoreConfig --strict --lib ES2022,DOM compile_fail/wide_string.ts
```

第一个错误说明 `Refund` 没有被处理：

```text
compile_fail/missing_case.ts(21,26): error TS2345: Argument of type 'Refund' is not assignable to parameter of type 'never'.
```

第二个错误说明普通 `string` 不能直接赋给 `"free" | "pro"`：

```text
compile_fail/wide_string.ts(10,3): error TS2322: Type 'string' is not assignable to type '"free" | "pro"'.
```

## 如何理解这些错误

第一类错误保护的是“新增业务类型时漏改分支”。如果系统新增退款事件 `Refund`，汇总逻辑、展示逻辑、埋点逻辑都可能需要处理它。`assertNever` 把漏处理的位置变成类型错误。

第二类错误保护的是“外部字符串直接进入受限字段”。CLI、HTTP、配置文件读出的字符串通常是普通 `string`，而业务字段 `plan` 只接受 `"free" | "pro"`。真实系统应该先解析和校验外部输入，再构造 `Signup`，不能把未经验证的字符串直接塞进去。

## 常见错误

**把 `as SomeType` 当成校验。** 类型断言会告诉编译器“相信我”，但它不会检查运行时数据。对外部输入，应先写解析函数或 schema 校验，再返回内部类型。

**把联合类型写得过宽。** 如果把 `kind` 写成 `string`，编译器就无法根据具体字面量缩小分支。判别联合要求每个分支都有稳定的字面量判别字段。

**只跑测试，不跑类型检查。** 测试只能覆盖被执行到的样例。类型检查能覆盖声明层面的所有路径，特别适合发现新增联合分支后漏改 `switch` 的问题。

**把 TypeScript 当成运行时边界。** TypeScript 编译后仍然是 JavaScript。类型检查不能替代 HTTP 输入校验、权限检查或反序列化检查。它适合保护代码内部的数据流和分支同步。

## 小结

TypeScript 的工程价值可以压缩成一句话：把 JavaScript 中隐含的对象形状和分支假设写成编译器能检查的约束。结构类型让模块之间按字段形状协作；narrowing 让分支内访问字段更安全；判别联合和 `assertNever` 让新增业务类型时的漏处理变成可定位错误。

这篇文章没有引入框架，也没有讨论前端构建。原因很简单：先把类型系统的核心机制讲清楚，后面再接 React、Node 服务或前端工程时，读者才知道类型错误究竟在保护什么。

## 练习

1. 给 `TrackingEvent` 增加 `Refund` 分支，观察 `applyEvent()` 和 `describeEvent()` 是否都被类型检查指出需要修改。
2. 写一个 `parseSignup(input: unknown): Signup`，只允许 `plan` 为 `"free"` 或 `"pro"`。
3. 删除 `isRevenueEvent()` 的 type predicate 返回类型，只返回 `boolean`，观察 `filter()` 后还能否直接访问 `amountCents`。
4. 把 `tsconfig.json` 中的 `strict` 改成 `false`，比较类型错误数量和错误质量。

## 参考资料

- [TypeScript Handbook: Everyday Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)
- [TypeScript Handbook: Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [TypeScript Handbook: Object Types](https://www.typescriptlang.org/docs/handbook/2/objects.html)
- [TypeScript TSConfig: strict](https://www.typescriptlang.org/tsconfig/strict.html)
- [Node.js: Running TypeScript with transpilation tools](https://nodejs.org/en/learn/typescript/run)
{% endraw %}
