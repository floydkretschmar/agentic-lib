import { readFileSync } from "node:fs"
import { basename, dirname, join, resolve } from "node:path"
import preToolUsePlugin from "./index.ts"

type ToolHookCallback = (event: ToolEvent) => Promise<void>

type ToolEvent = { tool: string; agent: string; input: Record<string, unknown> }

export const projectDirectory = resolve(import.meta.dirname, "../../..")

const siblingProjectFolderName = `${basename(projectDirectory)}-sibling`

export const siblingProjectNotesRelativePath = `../${siblingProjectFolderName}/notes.md`

export const siblingProjectNotesAbsolutePath = join(dirname(projectDirectory), siblingProjectFolderName, "notes.md")

const opencodeConfiguration = JSON.parse(readFileSync(join(projectDirectory, ".opencode/opencode.json"), "utf8"))

const configuredPluginOptions = opencodeConfiguration.plugins.find((pluginEntry) => pluginEntry.package === "./plugins/pre-tool-use").options

const rtkStubCommand = [
  process.execPath,
  "--eval",
  "process.stdout.write(JSON.stringify({ command: process.argv.slice(1).join('|') }))",
  "--",
]

export const failingCommand = [process.execPath, "--eval", "process.exit(1)"]

export const commandPrintingEmptyObject = [process.execPath, "--eval", "process.stdout.write('{}')"]

export const hangingCommand = [process.execPath, "--eval", "setTimeout(() => {}, 2000)"]

export function pluginOptionsWith(optionOverrides: Record<string, unknown>): Record<string, unknown> {
  return { ...configuredPluginOptions, rtkRewriteCommand: rtkStubCommand, ...optionOverrides }
}

export function pluginOptionsWithout(optionName: string): Record<string, unknown> {
  const pluginOptions = pluginOptionsWith({})
  delete pluginOptions[optionName]
  return pluginOptions
}

export async function setUpPlugin(pluginOptions: Record<string, unknown>): Promise<ToolHookCallback> {
  const registeredHooks = new Map<string, ToolHookCallback>()
  await preToolUsePlugin.setup({
    location: { directory: projectDirectory },
    options: pluginOptions,
    tool: { hook: async (hookName: string, callback: ToolHookCallback) => registeredHooks.set(hookName, callback) },
  })
  return registeredHooks.get("execute.before")
}

export function toolEvent(tool: string, input: Record<string, unknown>): ToolEvent {
  return { tool, agent: "build", input }
}
