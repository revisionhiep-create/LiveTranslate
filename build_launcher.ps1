# Build LiveTranslate.exe GUI launcher using Windows built-in csc.exe compiler
param(
    [string]$IconPath = "app.ico",
    [string]$OutExe = "LiveTranslate.exe"
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

$csSource = @"
using System;
using System.Diagnostics;
using System.IO;
using System.Threading;
using System.Windows.Forms;

namespace LiveTranslateLauncher
{
    static class Program
    {
        private const string AppMutexName = "Global\\LiveTranslate_App_SingleInstance_Mutex";
        private const string LauncherMutexName = "Global\\LiveTranslate_Launcher_SingleInstance_Mutex";

        [STAThread]
        static int Main(string[] args)
        {
            try
            {
                // Check if Python app is already running
                try
                {
                    Mutex existingApp = Mutex.OpenExisting(AppMutexName);
                    existingApp.Close();
                    MessageBox.Show(
                        "LiveTranslate is already running.\n\nPlease check your system tray or taskbar.",
                        "LiveTranslate",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Information
                    );
                    return 0;
                }
                catch (WaitHandleCannotBeOpenedException)
                {
                    // Not running
                }
                catch (Exception)
                {
                    // Ignore and proceed
                }

                // Prevent multiple concurrent launchers
                bool createdLauncher;
                using (Mutex launcherMutex = new Mutex(true, LauncherMutexName, out createdLauncher))
                {
                    if (!createdLauncher)
                    {
                        MessageBox.Show(
                            "LiveTranslate is already running or installation is in progress.",
                            "LiveTranslate",
                            MessageBoxButtons.OK,
                            MessageBoxIcon.Information
                        );
                        return 0;
                    }

                    string baseDir = AppDomain.CurrentDomain.BaseDirectory;
                Directory.SetCurrentDirectory(baseDir);

                // Add WinGet links to PATH
                string localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
                string winGetLinks = Path.Combine(localAppData, @"Microsoft\WinGet\Links");
                string currentPath = Environment.GetEnvironmentVariable("PATH") ?? "";
                if (Directory.Exists(winGetLinks) && !currentPath.Contains(winGetLinks))
                {
                    Environment.SetEnvironmentVariable("PATH", winGetLinks + ";" + currentPath);
                }

                // Check for venv python
                string venvDir = Path.Combine(baseDir, ".venv");
                string pythonwExe = Path.Combine(venvDir, @"Scripts\pythonw.exe");
                string pythonExe = Path.Combine(venvDir, @"Scripts\python.exe");

                string targetPython = File.Exists(pythonwExe) ? pythonwExe : (File.Exists(pythonExe) ? pythonExe : null);

                string readyMarker = Path.Combine(venvDir, ".livetranslate-ready");
                if (targetPython == null || !File.Exists(readyMarker))
                {
                    DialogResult res = MessageBox.Show(
                        "LiveTranslate requires a one-time environment setup to install dependencies (PyTorch/CUDA, ASR, translation).\n\nWould you like to start the automatic installation now?",
                        "LiveTranslate - Initial Setup",
                        MessageBoxButtons.YesNo,
                        MessageBoxIcon.Information
                    );
                    if (res == DialogResult.Yes)
                    {
                        string installBat = Path.Combine(baseDir, "install.bat");
                        if (!File.Exists(installBat))
                        {
                            MessageBox.Show("install.bat not found in " + baseDir, "LiveTranslate", MessageBoxButtons.OK, MessageBoxIcon.Error);
                            return 1;
                        }
                        ProcessStartInfo instPsi = new ProcessStartInfo();
                        instPsi.FileName = "cmd.exe";
                        instPsi.Arguments = "/c \"" + installBat + "\"";
                        instPsi.WorkingDirectory = baseDir;
                        instPsi.UseShellExecute = true;
                        using (Process instProc = Process.Start(instPsi))
                        {
                            if (instProc != null)
                            {
                                instProc.WaitForExit();
                            }
                        }
                        // Recheck python and ready marker
                        targetPython = File.Exists(pythonwExe) ? pythonwExe : (File.Exists(pythonExe) ? pythonExe : null);
                        if (targetPython == null || !File.Exists(readyMarker))
                        {
                            MessageBox.Show(
                                "Setup was not completed. You can run install.bat anytime.",
                                "LiveTranslate",
                                MessageBoxButtons.OK,
                                MessageBoxIcon.Warning
                            );
                            return 1;
                        }
                    }
                    else
                    {
                        return 0;
                    }
                }

                string mainScript = Path.Combine(baseDir, "main.py");
                if (!File.Exists(mainScript))
                {
                    MessageBox.Show(
                        "main.py not found in application directory.",
                        "LiveTranslate",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    );
                    return 1;
                }

                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = targetPython;
                psi.Arguments = "\"" + mainScript + "\"";
                if (args.Length > 0)
                {
                    psi.Arguments += " " + string.Join(" ", args);
                }
                psi.WorkingDirectory = baseDir;
                psi.UseShellExecute = false;
                psi.CreateNoWindow = true;

                using (Process proc = Process.Start(psi))
                {
                    if (proc == null)
                    {
                        MessageBox.Show("Failed to start LiveTranslate process.", "LiveTranslate", MessageBoxButtons.OK, MessageBoxIcon.Error);
                        return 1;
                    }
                    proc.WaitForExit();
                    if (proc.ExitCode != 0)
                    {
                        MessageBox.Show(
                            "LiveTranslate exited with error code " + proc.ExitCode + ".\nPlease check the logs in the 'logs' folder.",
                            "LiveTranslate",
                            MessageBoxButtons.OK,
                            MessageBoxIcon.Warning
                        );
                        return proc.ExitCode;
                    }
                    return 0;
                }
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    "Error launching LiveTranslate:\n" + ex.Message,
                    "LiveTranslate",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
                return 1;
            }
        }
    }
}
"@

$tempCs = Join-Path $ProjectDir "launcher_temp.cs"
Set-Content -Path $tempCs -Value $csSource -Encoding UTF8

$csc = "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if (-not (Test-Path $csc)) {
    $csc = "C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"
}

$targetIco = Join-Path $ProjectDir $IconPath
$targetExe = Join-Path $ProjectDir $OutExe

Write-Host "Compiling $OutExe with icon $IconPath..." -ForegroundColor Cyan
& $csc /target:winexe "/win32icon:$targetIco" "/out:$targetExe" $tempCs
if ($LASTEXITCODE -eq 0) {
    Remove-Item $tempCs -Force
    Write-Host "Build succeeded: $targetExe" -ForegroundColor Green
} else {
    Remove-Item $tempCs -Force -ErrorAction SilentlyContinue
    Write-Host "Build failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit 1
}

