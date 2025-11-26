# Validate Agent and Command File Sizes (PowerShell)
# Ensures files don't exceed Claude Code's practical token limits

$ErrorActionPreference = "Continue"

# Size limits
# Claude Code has a practical limit of ~25,000 tokens
# Using rough estimate of 4 characters per token = 100,000 characters
$HARD_LIMIT_CHARS = 100000  # ~25,000 tokens - will fail CI
$WARN_LIMIT_CHARS = 80000   # ~20,000 tokens - will show warning

# Counters
$script:totalFiles = 0
$script:oversizedFiles = 0
$script:warningFiles = 0

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Agent and Command File Size Validation" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Limits:"
Write-Host "  ⛔ Hard limit: 100,000 chars (~25,000 tokens)"
Write-Host "  ⚠️  Warning:    80,000 chars (~20,000 tokens)"
Write-Host ""

# Function to check a single file
function Test-FileSize {
    param([string]$FilePath)

    $content = Get-Content $FilePath -Raw
    $charCount = $content.Length
    $lineCount = (Get-Content $FilePath).Count
    $estimatedTokens = [math]::Floor($charCount / 4)

    if ($charCount -gt $HARD_LIMIT_CHARS) {
        Write-Host "❌ FAIL: $FilePath" -ForegroundColor Red
        Write-Host "   Size: $charCount chars (~$estimatedTokens tokens, $lineCount lines)"
        Write-Host "   Exceeds hard limit by $($charCount - $HARD_LIMIT_CHARS) characters"
        Write-Host ""
        $script:oversizedFiles++
        return $false
    }
    elseif ($charCount -gt $WARN_LIMIT_CHARS) {
        Write-Host "⚠️  WARN: $FilePath" -ForegroundColor Yellow
        Write-Host "   Size: $charCount chars (~$estimatedTokens tokens, $lineCount lines)"
        Write-Host "   Approaching limit ($WARN_LIMIT_CHARS chars)"
        Write-Host ""
        $script:warningFiles++
        return $true
    }
    else {
        Write-Host "✅ PASS: $FilePath" -ForegroundColor Green
        Write-Host "   Size: $charCount chars (~$estimatedTokens tokens, $lineCount lines)"
        return $true
    }
}

# Check all agent files
Write-Host "Checking agents\*.md files..."
Write-Host "--------------------------------------------------"
if (Test-Path "agents") {
    Get-ChildItem -Path "agents" -Filter "*.md" | ForEach-Object {
        Test-FileSize $_.FullName | Out-Null
        $script:totalFiles++
    }
}
else {
    Write-Host "⚠️  Warning: agents\ directory not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Checking .claude\commands\*.md files..."
Write-Host "--------------------------------------------------"
if (Test-Path ".claude\commands") {
    Get-ChildItem -Path ".claude\commands" -Filter "*.md" | ForEach-Object {
        Test-FileSize $_.FullName | Out-Null
        $script:totalFiles++
    }
}
else {
    Write-Host "⚠️  Warning: .claude\commands\ directory not found" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Total files checked: $script:totalFiles"
Write-Host "Files exceeding hard limit: $script:oversizedFiles" -ForegroundColor Red
Write-Host "Files with warnings: $script:warningFiles" -ForegroundColor Yellow
Write-Host ""

# Exit with failure if any files exceed hard limit
if ($script:oversizedFiles -gt 0) {
    Write-Host "❌ VALIDATION FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Files exceeding the hard limit (100,000 chars / ~25,000 tokens):"
    Write-Host "These files may cause performance issues or failures in Claude Code."
    Write-Host ""
    Write-Host "Recommended actions:"
    Write-Host "  1. Refactor large files to reduce size"
    Write-Host "  2. Move templates to separate files"
    Write-Host "  3. Remove verbose examples and duplicate content"
    Write-Host "  4. Extract common patterns to shared documentation"
    Write-Host ""
    Write-Host "See research/orchestrator-bloat-analysis.md for detailed guidance."
    Write-Host ""
    exit 1
}

if ($script:warningFiles -gt 0) {
    Write-Host "⚠️  WARNING" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Some files are approaching the size limit."
    Write-Host "Consider refactoring before adding more content."
    Write-Host ""
}

Write-Host "✅ All files within acceptable size limits" -ForegroundColor Green
exit 0
