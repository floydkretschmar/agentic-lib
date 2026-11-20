import assert from "node:assert/strict"
import { join } from "node:path"
import { test } from "node:test"
import {
  commandPrintingEmptyObject,
  failingCommand,
  hangingCommand,
  pluginOptionsWith,
  pluginOptionsWithout,
  projectDirectory,
  setUpPlugin,
  siblingProjectNotesAbsolutePath,
  siblingProjectNotesRelativePath,
  toolEvent,
} from "./pre-tool-use.fixture.ts"

test("blocks a tool call with the safety hook's reason", async (context) => {
  const blockedCalls = [
    { tool: "shell", input: { command: "git reset --hard HEAD" }, optionOverrides: {}, reason: "hard git resets are blocked" },
    { tool: "bash", input: { command: "rm -rf build" }, optionOverrides: {}, reason: "recursive forced deletion is blocked" },
    { tool: "write", input: { path: ".env", content: "" }, optionOverrides: {}, reason: "editing sensitive path is blocked: .env" },
    {
      tool: "edit",
      input: { path: join(projectDirectory, ".git/config"), oldString: "a", newString: "b" },
      optionOverrides: {},
      reason: "editing sensitive path is blocked: .git/config",
    },
    { tool: "write", input: { path: "/etc/hosts", content: "" }, optionOverrides: {}, reason: "editing sensitive path is blocked: /etc/hosts" },
    {
      tool: "write",
      input: { path: siblingProjectNotesRelativePath, content: "" },
      optionOverrides: {},
      reason: `editing sensitive path is blocked: ${siblingProjectNotesAbsolutePath}`,
    },
    {
      tool: "patch",
      input: { patchText: "*** Begin Patch\n*** Delete File: .git/config\n*** End Patch\n" },
      optionOverrides: {},
      reason: "editing sensitive path is blocked: .git/config",
    },
    { tool: "shell", input: { command: "git status" }, optionOverrides: { safetyHookCommand: failingCommand }, reason: /safety hook failed/ },
    { tool: "shell", input: { command: "git status" }, optionOverrides: { safetyHookCommand: commandPrintingEmptyObject }, reason: /safety hook returned no deny decision: \{\}/ },
    {
      tool: "shell",
      input: { command: "git status" },
      optionOverrides: { safetyHookCommand: hangingCommand, safetyHookTimeoutMilliseconds: 100 },
      reason: /safety hook failed/,
    },
    { tool: "shell", input: { workdir: "." }, optionOverrides: {}, reason: "shell input has no command" },
  ]

  for (const blockedCall of blockedCalls) {
    await context.test(`${blockedCall.tool} ${JSON.stringify(blockedCall.input)} ${JSON.stringify(blockedCall.optionOverrides)}`, async () => {
      const executeBefore = await setUpPlugin(pluginOptionsWith(blockedCall.optionOverrides))

      const toolCall = executeBefore(toolEvent(blockedCall.tool, blockedCall.input))

      await assert.rejects(toolCall, { message: blockedCall.reason })
    })
  }
})

test("lets an allowed tool call run with the rtk rewrite applied to shell commands", async (context) => {
  const glossaryPath = join(projectDirectory, "docs/GLOSSARY.md")
  const allowedCalls = [
    { tool: "shell", input: { command: "git status" }, optionOverrides: {}, expectedInput: { command: "--agent|build|git status" } },
    {
      tool: "edit",
      input: { path: glossaryPath, oldString: "a", newString: "b" },
      optionOverrides: {},
      expectedInput: { path: glossaryPath, oldString: "a", newString: "b" },
    },
    { tool: "read", input: { path: ".env" }, optionOverrides: {}, expectedInput: { path: ".env" } },
    { tool: "shell", input: { command: "git status" }, optionOverrides: { rtkRewriteCommand: failingCommand }, expectedInput: { command: "git status" } },
    {
      tool: "shell",
      input: { command: "git status" },
      optionOverrides: { rtkRewriteCommand: commandPrintingEmptyObject },
      expectedInput: { command: "git status" },
    },
  ]

  for (const allowedCall of allowedCalls) {
    await context.test(`${allowedCall.tool} ${JSON.stringify(allowedCall.input)} ${JSON.stringify(allowedCall.optionOverrides)}`, async () => {
      const executeBefore = await setUpPlugin(pluginOptionsWith(allowedCall.optionOverrides))
      const event = toolEvent(allowedCall.tool, allowedCall.input)

      await executeBefore(event)

      assert.deepEqual(event.input, allowedCall.expectedInput)
    })
  }
})

test("refuses to set up with a missing or wrongly typed option", async (context) => {
  const invalidPluginOptions = [
    { name: "without rtkRewriteCommand", pluginOptions: pluginOptionsWithout("rtkRewriteCommand"), reason: /rtkRewriteCommand/ },
    { name: "with a string timeout", pluginOptions: pluginOptionsWith({ safetyHookTimeoutMilliseconds: "5000" }), reason: /safetyHookTimeoutMilliseconds/ },
  ]

  for (const invalidOptions of invalidPluginOptions) {
    await context.test(invalidOptions.name, async () => {
      const setup = setUpPlugin(invalidOptions.pluginOptions)

      await assert.rejects(setup, { message: invalidOptions.reason })
    })
  }
})
