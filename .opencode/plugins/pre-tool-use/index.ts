import { execFile } from "node:child_process"
import { resolve } from "node:path"

type ToolEvent = { tool: string; agent: string; input: Record<string, unknown> }

type PluginContext = {
  location: { directory: string }
  options: Record<string, unknown>
  tool: { hook: (hookName: string, callback: (event: ToolEvent) => Promise<void>) => Promise<unknown> }
}

type ConfiguredCommand = { command: string[]; timeoutMilliseconds: number }

type SafetyHookMapping = { hookToolName: string; inputField: string; payloadField: string; inputIsPath: boolean }

const safetyHookMappingByTool: Record<string, SafetyHookMapping> = {
  shell: { hookToolName: "Bash", inputField: "command", payloadField: "command", inputIsPath: false },
  bash: { hookToolName: "Bash", inputField: "command", payloadField: "command", inputIsPath: false },
  patch: { hookToolName: "apply_patch", inputField: "patchText", payloadField: "command", inputIsPath: false },
  edit: { hookToolName: "Edit", inputField: "path", payloadField: "file_path", inputIsPath: true },
  write: { hookToolName: "Write", inputField: "path", payloadField: "file_path", inputIsPath: true },
}

function requiredCommandOption(options: Record<string, unknown>, optionName: string): string[] {
  const optionValue = options[optionName]
  if (!Array.isArray(optionValue) || optionValue.length === 0 || !optionValue.every((argument) => typeof argument === "string")) {
    throw new Error(`pre-tool-use option ${optionName} must be a non-empty array of strings`)
  }
  return optionValue
}

function requiredTimeoutOption(options: Record<string, unknown>, optionName: string): number {
  const optionValue = options[optionName]
  if (typeof optionValue !== "number" || !Number.isInteger(optionValue) || optionValue <= 0) {
    throw new Error(`pre-tool-use option ${optionName} must be a positive integer`)
  }
  return optionValue
}

function runCommand(configuredCommand: ConfiguredCommand, commandArguments: string[], standardInput: string, workingDirectory: string): Promise<string> {
  const [executable, ...configuredArguments] = configuredCommand.command
  return new Promise((resolveOutput, rejectOutput) => {
    const childProcess = execFile(
      executable,
      [...configuredArguments, ...commandArguments],
      { cwd: workingDirectory, timeout: configuredCommand.timeoutMilliseconds },
      (error, standardOutput) => (error ? rejectOutput(error) : resolveOutput(standardOutput)),
    )
    childProcess.stdin.on("error", rejectOutput)
    childProcess.stdin.end(standardInput)
  })
}

function denialReasonFrom(safetyHookOutput: string): string {
  const decision = JSON.parse(safetyHookOutput).hookSpecificOutput
  if (decision?.permissionDecision === "deny" && typeof decision.permissionDecisionReason === "string") {
    return decision.permissionDecisionReason
  }
  return `safety hook returned no deny decision: ${safetyHookOutput}`
}

export default {
  id: "pre-tool-use",
  async setup(context: PluginContext) {
    const safetyHook = {
      command: requiredCommandOption(context.options, "safetyHookCommand"),
      timeoutMilliseconds: requiredTimeoutOption(context.options, "safetyHookTimeoutMilliseconds"),
    }
    const rtkRewrite = {
      command: requiredCommandOption(context.options, "rtkRewriteCommand"),
      timeoutMilliseconds: requiredTimeoutOption(context.options, "rtkRewriteTimeoutMilliseconds"),
    }
    const projectDirectory = context.location.directory

    await context.tool.hook("execute.before", async (event) => {
      const safetyHookMapping = safetyHookMappingByTool[event.tool]
      if (safetyHookMapping === undefined) {
        return
      }

      const inputValue = event.input[safetyHookMapping.inputField]
      if (typeof inputValue !== "string") {
        throw new Error(`${event.tool} input has no ${safetyHookMapping.inputField}`)
      }

      const safetyHookPayload = {
        hook_event_name: "PreToolUse",
        tool_name: safetyHookMapping.hookToolName,
        tool_input: {
          [safetyHookMapping.payloadField]: safetyHookMapping.inputIsPath ? resolve(projectDirectory, inputValue) : inputValue,
        },
      }
      const safetyHookOutput = await runCommand(safetyHook, [], JSON.stringify(safetyHookPayload), projectDirectory).catch((error: Error) => {
        throw new Error(`safety hook failed: ${error.message}`)
      })
      if (safetyHookOutput !== "") {
        throw new Error(denialReasonFrom(safetyHookOutput))
      }

      if (safetyHookMapping.hookToolName !== "Bash") {
        return
      }

      const rewrittenCommand = await runCommand(rtkRewrite, ["--agent", event.agent, inputValue], "", projectDirectory)
        .then((rtkOutput) => JSON.parse(rtkOutput).command)
        .catch(() => undefined)
      if (typeof rewrittenCommand === "string" && rewrittenCommand !== "") {
        event.input.command = rewrittenCommand
      }
    })
  },
}
