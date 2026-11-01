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
using System.Windows.Forms;

namespace LiveTranslateLauncher
{
    static class Program
    {
        [STAThread]
        static int Main(string[] args)
        {
            try
            {
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

                if (targetPython == null)
                {
                    MessageBox.Show(
                        "Virtual environment not found.\nPlease run install.bat first to set up the environment.",
                        "LiveTranslate",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    );
                    return 1;
                }

                string readyMarker = Path.Combine(venvDir, ".livetranslate-ready");
                if (!File.Exists(readyMarker))
                {
                    MessageBox.Show(
                        "Virtual environment setup is incomplete.\nPlease run install.bat again to finish installing and verifying dependencies.",
                        "LiveTranslate",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Warning
                    );
                    return 1;
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

