<#
.SYNOPSIS
    Install the Claude Code skills in this repository.
    Default: spring-boot-ai and spring-boot-vsa. Other skills are installed by name.

.EXAMPLE
    .\install.ps1 -Personal
    .\install.ps1 -Project C:\code\my-spring-app
    .\install.ps1 -Personal -Skill spring-boot-vsa -Force
    .\install.ps1 -Project C:\code\my-app -Skill design-principles-review-by-max
#>
[CmdletBinding(DefaultParameterSetName = 'Interactive')]
param(
    [Parameter(ParameterSetName = 'Personal')]
    [switch]$Personal,

    [Parameter(ParameterSetName = 'Project', Mandatory = $true)]
    [string]$Project,

    [string[]]$Skill,

    [switch]$Force,

    [switch]$Help
)

$ErrorActionPreference = 'Stop'
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$AllSkills   = @('spring-boot-ai', 'spring-boot-vsa')
# Folders that hold skills: the repository root and each skill collection.
$SkillRoots  = @($ScriptDir, (Join-Path $ScriptDir 'custom-design-skills'))

if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Full
    exit 0
}

# Resolve scope (interactive fallback)
if ($PSCmdlet.ParameterSetName -eq 'Interactive') {
    Write-Host "Where should the skills be installed?"
    Write-Host "  1) Personal (all projects)"
    Write-Host "  2) A specific project"
    $choice = Read-Host "Choice [1/2]"
    switch ($choice) {
        '1' { $Personal = $true }
        '2' {
            $Project = Read-Host "Project path"
            if ([string]::IsNullOrWhiteSpace($Project)) { $Project = '.' }
        }
        default { Write-Error "Invalid choice."; exit 1 }
    }
}

# Resolve target root
if ($Personal) {
    $TargetRoot = Join-Path $env:USERPROFILE '.claude\skills'
}
else {
    $resolvedProject = (Resolve-Path -LiteralPath $Project -ErrorAction SilentlyContinue)
    if ($null -eq $resolvedProject) {
        New-Item -ItemType Directory -Path $Project -Force | Out-Null
        $resolvedProject = (Resolve-Path -LiteralPath $Project)
    }
    $TargetRoot = Join-Path $resolvedProject.Path '.claude\skills'
}

# Resolve which skills to install
if (-not $Skill -or $Skill.Count -eq 0) {
    $Skill = $AllSkills
}

New-Item -ItemType Directory -Path $TargetRoot -Force | Out-Null

foreach ($name in $Skill) {
    $src = $null
    foreach ($root in $SkillRoots) {
        $candidate = Join-Path $root $name
        if (Test-Path -LiteralPath (Join-Path $candidate 'SKILL.md') -PathType Leaf) {
            $src = $candidate
            break
        }
    }
    $dest = Join-Path $TargetRoot $name

    if ($null -eq $src) {
        Write-Warning "Skipping ${name}: no such skill in $ScriptDir or its custom-design-skills folder"
        continue
    }

    if (Test-Path -LiteralPath $dest) {
        if (-not $Force) {
            $ans = Read-Host "$dest already exists. Overwrite? [y/N]"
            if ($ans -notmatch '^(y|yes)$') {
                Write-Host "  -> skipped"
                continue
            }
        }
        Remove-Item -LiteralPath $dest -Recurse -Force
    }

    Copy-Item -LiteralPath $src -Destination $dest -Recurse
    Write-Host "Installed $name -> $dest"
}

Write-Host ""
Write-Host "Done. Open Claude Code in the project and try:"
Write-Host '  - "scaffold a new payment feature slice"   (triggers spring-boot-vsa)'
Write-Host '  - "how do I parse this LLM JSON into a Java record"   (triggers spring-boot-ai)'
Write-Host '  - "run a design principles review of this screen"   (triggers design-principles-review-by-max)'
