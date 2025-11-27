# Validate Skills Structure and Invocation (PowerShell)
# Ensures skills follow the skill-implementation-guide.md requirements

$ErrorActionPreference = "Continue"

# Counters
$script:totalSkills = 0
$script:failedSkills = 0
$script:warningSkills = 0

# Size guidelines (lines)
$IDEAL_MAX_LINES = 250
$WARNING_LINES = 150

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Skills Structure Validation" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Validating against: research/skill-implementation-guide.md"
Write-Host ""

# Function to check a single skill
function Test-Skill {
    param([string]$SkillDir)

    $skillName = Split-Path $SkillDir -Leaf
    $hasErrors = $false
    $hasWarnings = $false

    Write-Host "📦 Checking skill: $skillName"
    Write-Host "--------------------------------------------------"

    $skillMdPath = Join-Path $SkillDir "SKILL.md"

    # Check 1: SKILL.md exists
    if (-not (Test-Path $skillMdPath)) {
        Write-Host "  ❌ FAIL: SKILL.md not found" -ForegroundColor Red
        $hasErrors = $true
    }
    else {
        Write-Host "  ✅ SKILL.md exists" -ForegroundColor Green

        $content = Get-Content $skillMdPath -Raw

        # Check 2: Frontmatter fields (use multiline mode for ^ anchor)
        $hasVersion = $content -match "(?m)^version:"
        $hasName = $content -match "(?m)^name:"
        $hasDescription = $content -match "(?m)^description:"

        if (-not $hasVersion) {
            Write-Host "  ❌ FAIL: Missing 'version' in frontmatter" -ForegroundColor Red
            $hasErrors = $true
        }
        else {
            Write-Host "  ✅ Has 'version' field" -ForegroundColor Green
        }

        if (-not $hasName) {
            Write-Host "  ❌ FAIL: Missing 'name' in frontmatter" -ForegroundColor Red
            $hasErrors = $true
        }
        else {
            # Check if name matches directory (multiline mode)
            if ($content -match "(?m)^name:\s*(\S+)") {
                $frontmatterName = $matches[1]
                if ($frontmatterName -ne $skillName) {
                    Write-Host "  ❌ FAIL: Name mismatch (frontmatter: '$frontmatterName', directory: '$skillName')" -ForegroundColor Red
                    $hasErrors = $true
                }
                else {
                    Write-Host "  ✅ Name matches directory: $frontmatterName" -ForegroundColor Green
                }
            }
        }

        if (-not $hasDescription) {
            Write-Host "  ❌ FAIL: Missing 'description' in frontmatter" -ForegroundColor Red
            $hasErrors = $true
        }
        else {
            Write-Host "  ✅ Has 'description' field" -ForegroundColor Green
        }

        # Check 3: Required sections
        $hasWhenToInvoke = $content -match "## When to Invoke"
        $hasYourTask = $content -match "## Your Task"

        if (-not $hasWhenToInvoke) {
            Write-Host "  ⚠️  WARN: Missing '## When to Invoke' section" -ForegroundColor Yellow
            $hasWarnings = $true
        }
        else {
            Write-Host "  ✅ Has 'When to Invoke' section" -ForegroundColor Green
        }

        if (-not $hasYourTask) {
            Write-Host "  ⚠️  WARN: Missing '## Your Task' section" -ForegroundColor Yellow
            $hasWarnings = $true
        }
        else {
            Write-Host "  ✅ Has 'Your Task' section" -ForegroundColor Green
        }

        # Check 4: File size
        $lineCount = (Get-Content $skillMdPath).Count

        if ($lineCount -gt $IDEAL_MAX_LINES) {
            Write-Host "  ⚠️  WARN: SKILL.md has $lineCount lines (ideal: <$IDEAL_MAX_LINES)" -ForegroundColor Yellow
            Write-Host "      Consider moving verbose content to references/usage.md" -ForegroundColor Yellow
            $hasWarnings = $true
        }
        elseif ($lineCount -gt $WARNING_LINES) {
            Write-Host "  ✅ Size acceptable: $lineCount lines" -ForegroundColor Green
        }
        else {
            Write-Host "  ✅ Size good: $lineCount lines" -ForegroundColor Green
        }
    }

    Write-Host ""

    if ($hasErrors) {
        $script:failedSkills++
        return $false
    }
    elseif ($hasWarnings) {
        $script:warningSkills++
    }

    return $true
}

# Function to check skill invocations in agent files
function Test-Invocations {
    Write-Host "🔍 Checking skill invocations in agent files..."
    Write-Host "--------------------------------------------------"

    $badInvocations = 0

    if (Test-Path "agents") {
        Get-ChildItem -Path "agents" -Filter "*.md" | ForEach-Object {
            $content = Get-Content $_.FullName -Raw
            if ($content -match "Skill\(skill:") {
                Write-Host "❌ FAIL: $($_.FullName) has incorrect invocation syntax" -ForegroundColor Red
                Write-Host "  Should use: Skill(command: `"skill-name`")" -ForegroundColor Yellow
                Write-Host "  Not:        Skill(skill: `"skill-name`")" -ForegroundColor Yellow
                Write-Host ""
                $badInvocations++
            }
        }
    }

    if (Test-Path ".claude\commands") {
        Get-ChildItem -Path ".claude\commands" -Filter "*.md" | ForEach-Object {
            $content = Get-Content $_.FullName -Raw
            if ($content -match "Skill\(skill:") {
                Write-Host "❌ FAIL: $($_.FullName) has incorrect invocation syntax" -ForegroundColor Red
                Write-Host "  Should use: Skill(command: `"skill-name`")" -ForegroundColor Yellow
                Write-Host "  Not:        Skill(skill: `"skill-name`")" -ForegroundColor Yellow
                Write-Host ""
                $badInvocations++
            }
        }
    }

    if ($badInvocations -eq 0) {
        Write-Host "✅ All skill invocations use correct syntax" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Found $badInvocations file(s) with incorrect invocation syntax" -ForegroundColor Red
        return $false
    }

    Write-Host ""
    return $true
}

# Main validation
Write-Host "Checking all skills in .claude\skills\..."
Write-Host ""

if (-not (Test-Path ".claude\skills")) {
    Write-Host "❌ ERROR: .claude\skills\ directory not found" -ForegroundColor Red
    exit 1
}

# Check each skill
Get-ChildItem -Path ".claude\skills" -Directory | ForEach-Object {
    Test-Skill $_.FullName | Out-Null
    $script:totalSkills++
}

# Check invocations
$invocationCheckPassed = Test-Invocations

# Summary
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Total skills checked: $script:totalSkills"
Write-Host "Skills with errors: $script:failedSkills" -ForegroundColor Red
Write-Host "Skills with warnings: $script:warningSkills" -ForegroundColor Yellow
Write-Host ""

# Exit with failure if any skills have errors or bad invocations
if (($script:failedSkills -gt 0) -or (-not $invocationCheckPassed)) {
    Write-Host "❌ VALIDATION FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Errors found in skill structure or invocation syntax."
    Write-Host ""
    Write-Host "To fix:"
    Write-Host "  1. Review the errors flagged above"
    Write-Host "  2. See research/skill-implementation-guide.md for requirements"
    Write-Host "  3. See research/skill-fix-manual.md for step-by-step fixing"
    Write-Host ""
    Write-Host "Common fixes:"
    Write-Host "  - Add missing frontmatter fields (version, name, description)"
    Write-Host "  - Ensure name in frontmatter matches directory name"
    Write-Host "  - Add missing sections (When to Invoke, Your Task)"
    Write-Host "  - Fix invocation syntax: Skill(command:) not Skill(skill:)"
    Write-Host ""
    exit 1
}

if ($script:warningSkills -gt 0) {
    Write-Host "⚠️  WARNING" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Some skills have warnings (non-critical)."
    Write-Host "Consider addressing these to improve skill quality."
    Write-Host ""
}

Write-Host "✅ All skills properly structured" -ForegroundColor Green
exit 0
