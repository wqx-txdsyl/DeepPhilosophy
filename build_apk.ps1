# Build APK script for DeepPhilosophy
$ErrorActionPreference = "Stop"

# Set Java home to actual JDK
$env:JAVA_HOME = "C:\Program Files\Common Files\Oracle\Java\javapath_target_1863468140"

Write-Host "JAVA_HOME: $env:JAVA_HOME"
Write-Host "Building APK..."

Set-Location "$PSScriptRoot\app\android"

# Run Gradle
.\gradlew assembleDebug

if ($LASTEXITCODE -eq 0) {
    $apkPath = Get-ChildItem -Path "app\build\outputs\apk\debug" -Filter "*.apk" -Recurse | Select-Object -First 1
    Write-Host "APK built successfully!"
    Write-Host "Location: $($apkPath.FullName)"
} else {
    Write-Host "Build failed with exit code $LASTEXITCODE"
}
