import * as child_process from "child_process";
import * as fs from "fs";
import * as path from "path";
import * as vscode from "vscode";
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
} from "vscode-languageclient/node";

let client: LanguageClient | undefined;
let status: vscode.StatusBarItem | undefined;

export async function activate(context: vscode.ExtensionContext): Promise<void> {
  const config = vscode.workspace.getConfiguration("puzzleDsl");
  if (!config.get<boolean>("enable", true)) {
    return;
  }

  status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  status.command = "puzzleDsl.showOutput";
  context.subscriptions.push(status);

  const showOutput = vscode.commands.registerCommand("puzzleDsl.showOutput", () => {
    client?.outputChannel.show();
  });
  context.subscriptions.push(showOutput);

  const folder = vscode.workspace.workspaceFolders?.[0];
  if (!folder) {
    status.text = "Puzzle DSL: no workspace";
    status.show();
    return;
  }
  const cwd = folder.uri.fsPath;
  const marker = path.join(cwd, "puzzle", "dsl", "__init__.py");
  if (!fs.existsSync(marker)) {
    void vscode.window.showErrorMessage(
      "Puzzle DSL: open the logic_solver repository root (folder containing puzzle/dsl/) so the language server can start."
    );
    status.text = "Puzzle DSL: not a repo root";
    status.show();
    return;
  }

  const python = await findPython(config.get<string>("pythonPath") || "", cwd);
  if (!python) {
    const pick = await vscode.window.showErrorMessage(
      "Puzzle DSL needs Python 3.10+ on PATH (or set puzzleDsl.pythonPath). Syntax highlighting still works.",
      "Open Settings"
    );
    if (pick === "Open Settings") {
      await vscode.commands.executeCommand(
        "workbench.action.openSettings",
        "puzzleDsl.pythonPath"
      );
    }
    status.text = "Puzzle DSL: no Python";
    status.show();
    return;
  }

  const level = config.get<string>("diagnostics.level") || "semantic";
  const serverOptions: ServerOptions = {
    command: python,
    args: ["-m", "puzzle.lsp"],
    options: { cwd },
  };
  const clientOptions: LanguageClientOptions = {
    documentSelector: [{ language: "puzzle-dsl", scheme: "file" }],
    synchronize: {
      configurationSection: "puzzleDsl",
      fileEvents: vscode.workspace.createFileSystemWatcher("**/*.dsl"),
    },
    initializationOptions: {
      diagnosticsLevel: level,
    },
    outputChannelName: "Puzzle DSL",
  };

  client = new LanguageClient(
    "puzzleDsl",
    "Puzzle DSL",
    serverOptions,
    clientOptions
  );

  try {
    await client.start();
  } catch (err) {
    void vscode.window.showErrorMessage(
      `Puzzle DSL language server failed to start: ${err instanceof Error ? err.message : String(err)}`
    );
    status.text = "Puzzle DSL: failed";
    status.show();
    return;
  }

  const label = level === "off" ? "off" : level === "syntax" ? "syntax (T1)" : "semantic (T1/T2)";
  status.text = `Puzzle DSL: ${label}`;
  status.tooltip = "Language server running. Library files get syntax diagnostics only.";
  status.show();
}

export async function deactivate(): Promise<void> {
  if (client) {
    await client.stop();
    client = undefined;
  }
}

async function findPython(configured: string, cwd: string): Promise<string | undefined> {
  const fallback =
    process.platform === "win32" ? ["python", "python3"] : ["python3", "python"];
  const candidates = configured ? [configured] : fallback;
  for (const cmd of candidates) {
    if (await pythonOk(cmd, cwd)) {
      return cmd;
    }
  }
  return undefined;
}

function pythonOk(cmd: string, cwd: string): Promise<boolean> {
  return new Promise((resolve) => {
    const child = child_process.spawn(
      cmd,
      ["-c", "import sys, puzzle.lsp; sys.exit(0 if sys.version_info >= (3, 10) else 1)"],
      { cwd, stdio: "ignore" }
    );
    const timer = setTimeout(() => {
      child.kill();
      resolve(false);
    }, 5000);
    child.on("error", () => {
      clearTimeout(timer);
      resolve(false);
    });
    child.on("exit", (code) => {
      clearTimeout(timer);
      resolve(code === 0);
    });
  });
}
