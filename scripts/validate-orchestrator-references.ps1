# Validate and auto-fix orchestrator.md section references (PowerShell)
# Supports: §line XXXX (keyword), §Step X.Y.Z, orphan detection, auto-fix

param(
    [switch]$Fix,
    [switch]$CheckOrphans,
    [switch]$Detailed  # Renamed from $Verbose to avoid shadowing built-in parameter
)

$ErrorActionPreference = "Continue"

$ORCHESTRATOR_FILE = "agents\orchestrator.md"
$script:Errors = 0
$script:Warnings = 0

Write-Host "🔍 Validating orchestrator.md references..."
if ($Fix) { Write-Host "   🔧 Auto-fix mode enabled" }
if ($CheckOrphans) { Write-Host "   🔍 Orphan detection enabled" }

if (-not (Test-Path $ORCHESTRATOR_FILE)) {
    Write-Host "❌ Error: $ORCHESTRATOR_FILE not found" -ForegroundColor Red
    exit 1
}

$content = Get-Content $ORCHESTRATOR_FILE
$totalLines = $content.Count

# Feature 1: Content Validation with Keywords
function Test-LineReferences {
    $lineRefs = [regex]::Matches((Get-Content $ORCHESTRATOR_FILE -Raw), '§line (\d+)( \(([^)]+)\))?') |
        Select-Object -Property @{N='LineNum';E={[int]$_.Groups[1].Value}}, @{N='Keyword';E={$_.Groups[3].Value}} -Unique

    if ($lineRefs.Count -eq 0) { return }

    Write-Host "  → Found $($lineRefs.Count) unique §line references"

    foreach ($ref in $lineRefs) {
        $lineNum = $ref.LineNum
        $keyword = $ref.Keyword

        if ($lineNum -gt $totalLines) {
            if ($Fix -and $keyword) {
                # Try to find content by keyword
                $searchResult = Select-String -Path $ORCHESTRATOR_FILE -Pattern $keyword -CaseSensitive:$false | Select-Object -First 1
                if ($searchResult) {
                    $newLine = $searchResult.LineNumber
                    Write-Host "  🔧 AUTO-FIX: §line $lineNum → §line $newLine (found '$keyword' at line $newLine)"
                    $fileContent = Get-Content $ORCHESTRATOR_FILE -Raw
                    # Use word boundary pattern to avoid replacing partial matches (e.g., §line 14 in §line 140)
                    $fileContent = $fileContent -replace "§line $lineNum(?!\d)", "§line $newLine"
                    Set-Content -Path $ORCHESTRATOR_FILE -Value $fileContent
                    continue
                }
            }
            Write-Host "  ❌ BROKEN: §line $lineNum (file only has $totalLines lines)" -ForegroundColor Red
            if ($keyword) { Write-Host "      Expected keyword: '$keyword'" }
            if (-not $Fix) { Write-Host "      Hint: Run with -Fix to auto-update" }
            $script:Errors++
            continue
        }

        # Validate content if keyword is provided
        if ($keyword) {
            $actualLine = $content[$lineNum - 1]
            if ($actualLine -notmatch [regex]::Escape($keyword)) {
                if ($Fix) {
                    $searchResult = Select-String -Path $ORCHESTRATOR_FILE -Pattern $keyword -CaseSensitive:$false | Select-Object -First 1
                    if ($searchResult -and $searchResult.LineNumber -ne $lineNum) {
                        $newLine = $searchResult.LineNumber
                        Write-Host "  🔧 AUTO-FIX: §line $lineNum → §line $newLine (content mismatch, found '$keyword' at line $newLine)"
                        $fileContent = Get-Content $ORCHESTRATOR_FILE -Raw
                        # Use word boundary pattern to avoid replacing partial matches (e.g., §line 14 in §line 140)
                        $fileContent = $fileContent -replace "§line $lineNum(?!\d)", "§line $newLine"
                        Set-Content -Path $ORCHESTRATOR_FILE -Value $fileContent
                        continue
                    }
                }
                Write-Host "  ⚠️  CONTENT MISMATCH: §line $lineNum" -ForegroundColor Yellow
                Write-Host "      Expected keyword: '$keyword'"
                Write-Host "      Actual content: $actualLine"
                $script:Warnings++
            }
            elseif ($Detailed) {
                Write-Host "  ✅ §line $lineNum: '$keyword' ✓" -ForegroundColor Green
            }
        }
    }
}

# Feature 2: Step Reference Validation
function Test-StepReferences {
    $stepRefs = [regex]::Matches((Get-Content $ORCHESTRATOR_FILE -Raw), '§Step ([0-9A-Z]+\.[0-9A-Z]+(\.[0-9]+)?)') |
        Select-Object -Property @{N='StepId';E={$_.Groups[1].Value}} -Unique

    if ($stepRefs.Count -eq 0) { return }

    Write-Host "  → Found $($stepRefs.Count) unique §Step references"

    foreach ($ref in $stepRefs) {
        $stepId = $ref.StepId
        $searchResult = Select-String -Path $ORCHESTRATOR_FILE -Pattern "### Step $stepId" | Select-Object -First 1

        if (-not $searchResult) {
            Write-Host "  ❌ BROKEN: §Step $stepId (section not found)" -ForegroundColor Red
            Write-Host "      Searching for: ### Step $stepId"
            Write-Host "      Note: §Step references cannot be auto-fixed (section structure changed)"
            $script:Errors++
        }
        elseif ($Detailed) {
            Write-Host "  ✅ §Step $stepId → line $($searchResult.LineNumber)" -ForegroundColor Green
        }
    }
}

# Feature 3: Reverse Lookup - Find Orphaned Sections
function Test-OrphanedSections {
    if (-not $CheckOrphans) { return }

    Write-Host ""
    Write-Host "🔍 Checking for orphaned sections (not referenced anywhere)..."

    $orphanSteps = 0
    $fileContent = Get-Content $ORCHESTRATOR_FILE -Raw

    Select-String -Path $ORCHESTRATOR_FILE -Pattern "^### Step ([0-9A-Z]+\.[0-9A-Z]+(\.[0-9]+)?)" | ForEach-Object {
        if ($_.Matches[0].Groups[1].Value) {
            $stepId = $_.Matches[0].Groups[1].Value
            if ($fileContent -notmatch "§Step $stepId") {
                Write-Host "  ⚠️  ORPHAN: ### Step $stepId (line $($_.LineNumber)) - not referenced" -ForegroundColor Yellow
                $orphanSteps++
            }
        }
    }

    if ($orphanSteps -eq 0) {
        Write-Host "  ✅ No orphaned sections found" -ForegroundColor Green
    }
    else {
        Write-Host ""
        Write-Host "  Found $orphanSteps orphaned step(s)"
        Write-Host "  Note: Orphans are not errors, but may indicate unused sections"
    }
}

# Run validations
Test-LineReferences
Test-StepReferences
Test-OrphanedSections

# Summary
Write-Host ""
if (($script:Errors -eq 0) -and ($script:Warnings -eq 0)) {
    Write-Host "✅ All references are valid" -ForegroundColor Green
    if ($Fix) { Write-Host "   No fixes were needed" }
    exit 0
}
elseif (($script:Errors -eq 0) -and ($script:Warnings -gt 0)) {
    Write-Host "⚠️  Validation passed with $($script:Warnings) warning(s)" -ForegroundColor Yellow
    Write-Host "   Warnings indicate content mismatches but won't block commits"
    exit 0
}
else {
    Write-Host "❌ Validation failed: $($script:Errors) error(s), $($script:Warnings) warning(s)" -ForegroundColor Red
    Write-Host ""
    if ($Fix) {
        Write-Host "Some references could not be auto-fixed."
        Write-Host "Manual intervention required:"
        Write-Host "  1. Review the errors above"
        Write-Host "  2. Update references manually"
        Write-Host "  3. Run validation again"
    }
    else {
        Write-Host "To auto-fix broken references:"
        Write-Host "  .\scripts\validate-orchestrator-references.ps1 -Fix"
        Write-Host ""
        Write-Host "To manually fix:"
        Write-Host "  1. Search for the broken reference in $ORCHESTRATOR_FILE"
        Write-Host "  2. Find where the target content actually is now"
        Write-Host "  3. Update the reference to point to the correct line/step"
    }
    exit 1
}
