<#
.SYNOPSIS
    Install the Claude Code skills in this repository.
    Default: spring-boot-ai and spring-boot-vsa. Other skills are installed by name.

.EXAMPLE
    .\install.ps1 -Personal
    .\install.ps1 -Project C:\code\my-spring-app
    .\install.ps1 -Personal -Skill spring-boot-vsa -Force
    .\install.ps1 -Project C:\code\my-app -Skill design-principles-review-by-max
    .\install.ps1 -Project C:\code\my-app -Skill design-principles-review-by-max -Agent antigravity

.PARAMETER Agent
    The coding agent: claude (default), codex or antigravity.
      claude       <project>\.claude\skills   or  ~\.claude\skills
      codex        <project>\.agents\skills   or  ~\.agents\skills
      antigravity  <project>\.agents\skills   or  ~\.gemini\config\skills
#>
[CmdletBinding(DefaultParameterSetName = 'Interactive')]
param(
    [Parameter(ParameterSetName = 'Personal')]
    [switch]$Personal,

    [Parameter(ParameterSetName = 'Project', Mandatory = $true)]
    [string]$Project,

    [string[]]$Skill,

    [ValidateSet('claude', 'codex', 'antigravity')]
    [string]$Agent = 'claude',

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

# Folder per agent, relative to the project or to the home folder
$ProjectDir  = @{ claude = '.claude\skills'; codex = '.agents\skills'; antigravity = '.agents\skills' }[$Agent]
$PersonalDir = @{ claude = '.claude\skills'; codex = '.agents\skills'; antigravity = '.gemini\config\skills' }[$Agent]

# Resolve target root
if ($Personal) {
    $TargetRoot = Join-Path $env:USERPROFILE $PersonalDir
}
else {
    $resolvedProject = (Resolve-Path -LiteralPath $Project -ErrorAction SilentlyContinue)
    if ($null -eq $resolvedProject) {
        New-Item -ItemType Directory -Path $Project -Force | Out-Null
        $resolvedProject = (Resolve-Path -LiteralPath $Project)
    }
    $TargetRoot = Join-Path $resolvedProject.Path $ProjectDir
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
$AgentName = @{ claude = 'Claude Code'; codex = 'Codex'; antigravity = 'Antigravity' }[$Agent]
$Prefix    = @{ claude = '/'; codex = '$'; antigravity = '/' }[$Agent]
Write-Host "Done. Start a new $AgentName session in the project and try:"
foreach ($name in $Skill) {
    switch ($name) {
        'spring-boot-vsa'        { Write-Host '  - "scaffold a new payment feature slice"   (uses spring-boot-vsa)' }
        'spring-boot-ai'         { Write-Host '  - "how do I parse this LLM JSON into a Java record"   (uses spring-boot-ai)' }
        'angular-vertical-slice' { Write-Host '  - "add an invoices feature using our Angular conventions"   (uses angular-vertical-slice)' }
        'design-principles-review-by-max' { Write-Host "  - ${Prefix}design-principles-review-by-max help" }
    }
}
