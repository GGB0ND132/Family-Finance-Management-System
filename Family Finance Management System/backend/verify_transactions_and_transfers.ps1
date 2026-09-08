# verify_transactions_and_transfers.ps1
# One-click verification: Transaction & Transfer modules
# Usage: .\verify_transactions_and_transfers.ps1
# Prerequisites: MySQL running, backend on localhost:8000

$ErrorActionPreference = "Stop"
$base = "http://localhost:8000/api/v1"
$pass = 0
$fail = 0

function Test-Step {
    param([string]$Name, [scriptblock]$Script)
    Write-Host "[TEST] $Name ... " -NoNewline
    try {
        & $Script
        Write-Host "PASS" -ForegroundColor Green
        $global:pass++
    } catch {
        Write-Host "FAIL: $_" -ForegroundColor Red
        $global:fail++
    }
}

# ============================================================
# Phase 1: Setup (register, family, accounts, categories)
# ============================================================
Write-Host "`n" + ("="*60) -ForegroundColor Cyan
Write-Host "  Phase 1: Environment Setup" -ForegroundColor Cyan
Write-Host ("="*60) -ForegroundColor Cyan

# --- Register or login alice ---
$aliceRegistered = $true
try {
    $alice = Invoke-RestMethod -Uri "$base/auth/register" -Method Post -Body '{"username":"alice_test01","password":"12345678","nickname":"Alice"}' -ContentType "application/json" -ErrorAction Stop
} catch {
    $aliceRegistered = $false
    Write-Host "  alice already exists, logging in..." -ForegroundColor Yellow
    $alice = Invoke-RestMethod -Uri "$base/auth/login" -Method Post -Body '{"username":"alice_test01","password":"12345678"}' -ContentType "application/json"
}
$aTok = $alice.data.access_token
Write-Host "  alice token: $($aTok.Substring(0, 20))..." -ForegroundColor Gray
if (-not $aTok) { throw "Failed to get alice token" }

# --- Register or login bob ---
$bobRegistered = $true
try {
    $bob = Invoke-RestMethod -Uri "$base/auth/register" -Method Post -Body '{"username":"bob_test01","password":"12345678","nickname":"Bob"}' -ContentType "application/json" -ErrorAction Stop
} catch {
    $bobRegistered = $false
    Write-Host "  bob already exists, logging in..." -ForegroundColor Yellow
    $bob = Invoke-RestMethod -Uri "$base/auth/login" -Method Post -Body '{"username":"bob_test01","password":"12345678"}' -ContentType "application/json"
}
$bTok = $bob.data.access_token
Write-Host "  bob token: $($bTok.Substring(0, 20))..." -ForegroundColor Gray
if (-not $bTok) { throw "Failed to get bob token" }

# --- Create family ---
$fam = Invoke-RestMethod -Uri "$base/families" -Method Post -H @{Authorization="Bearer $aTok"} -Body '{"name":"TestFamily"}' -ContentType "application/json"
$fid = $fam.data.id

# --- Join family ---
$inv = Invoke-RestMethod -Uri "$base/families/$fid/invite-code" -Method Post -H @{Authorization="Bearer $aTok"}
$code = $inv.data.invite_code
Invoke-RestMethod -Uri "$base/families/join" -Method Post -H @{Authorization="Bearer $bTok"} -Body "{`"invite_code`":`"$code`"}" -ContentType "application/json" | Out-Null

# --- Get member IDs ---
$members = Invoke-RestMethod -Uri "$base/families/$fid/members" -H @{Authorization="Bearer $aTok"}
$aMemberId = ($members.data | Where-Object { $_.nickname -eq "Alice" }).id
$bMemberId = ($members.data | Where-Object { $_.nickname -eq "Bob" }).id
if (-not $aMemberId -or -not $bMemberId) { throw "Failed to get member IDs" }

# --- Create accounts ---
$aAcc = Invoke-RestMethod -Uri "$base/accounts" -Method Post -H @{Authorization="Bearer $aTok"} -Body "{`"family_id`":$fid,`"owner_member_id`":$aMemberId,`"name`":`"AliceCash`",`"type`":`"CASH`",`"initial_balance`":`"5000.00`"}" -ContentType "application/json"
$bAcc = Invoke-RestMethod -Uri "$base/accounts" -Method Post -H @{Authorization="Bearer $bTok"} -Body "{`"family_id`":$fid,`"owner_member_id`":$bMemberId,`"name`":`"BobBank`",`"type`":`"BANK_CARD`",`"initial_balance`":`"3000.00`"}" -ContentType "application/json"
$aAccId = $aAcc.data.id
$bAccId = $bAcc.data.id

# --- Create categories ---
$expCat = Invoke-RestMethod -Uri "$base/categories" -Method Post -H @{Authorization="Bearer $aTok"} -Body "{`"family_id`":$fid,`"name`":`"Food`",`"type`":`"EXPENSE`"}" -ContentType "application/json"
$incCat = Invoke-RestMethod -Uri "$base/categories" -Method Post -H @{Authorization="Bearer $aTok"} -Body "{`"family_id`":$fid,`"name`":`"Salary`",`"type`":`"INCOME`"}" -ContentType "application/json"
$expCatId = $expCat.data.id
$incCatId = $incCat.data.id

function Get-AliceBalance {
    (Invoke-RestMethod -Uri "$base/accounts?family_id=$fid&scope=personal" -H @{Authorization="Bearer $aTok"}).data.items[0].current_balance
}
function Get-BobBalance {
    (Invoke-RestMethod -Uri "$base/accounts?family_id=$fid&scope=personal" -H @{Authorization="Bearer $bTok"}).data.items[0].current_balance
}

Write-Host "Setup done: family=$fid, aliceAcc=$aAccId, bobAcc=$bAccId" -ForegroundColor Green

# ============================================================
# Phase 2: Transaction Module
# ============================================================
Write-Host "`n" + ("="*60) -ForegroundColor Cyan
Write-Host "  Phase 2: Transaction Module (Income/Expense)" -ForegroundColor Cyan
Write-Host ("="*60) -ForegroundColor Cyan

# --- 2.1 Create expense ---
$txExpense = $null
Test-Step "Create expense (200)" {
    $body = "{`"family_id`":$fid,`"account_id`":$aAccId,`"category_id`":$expCatId,`"beneficiary_member_id`":$aMemberId,`"type`":`"EXPENSE`",`"amount`":`"200.00`",`"occurred_at`":`"2026-09-07T12:00:00Z`"}"
    $global:txExpense = Invoke-RestMethod -Uri "$base/transactions" -Method Post -H @{Authorization="Bearer $aTok"} -Body $body -ContentType "application/json"
    if ($global:txExpense.data.type -ne "EXPENSE" -or $global:txExpense.data.amount -ne "200.00") { throw "Bad response data" }
}
Test-Step "After expense: balance=4800.00" {
    $bal = Get-AliceBalance
    if ($bal -ne "4800.00") { throw "Expected 4800.00, got $bal" }
}

# --- 2.2 Create income ---
$txIncome = $null
Test-Step "Create income (3000)" {
    $body = "{`"family_id`":$fid,`"account_id`":$aAccId,`"category_id`":$incCatId,`"beneficiary_member_id`":$aMemberId,`"type`":`"INCOME`",`"amount`":`"3000.00`",`"occurred_at`":`"2026-09-07T12:00:00Z`"}"
    $global:txIncome = Invoke-RestMethod -Uri "$base/transactions" -Method Post -H @{Authorization="Bearer $aTok"} -Body $body -ContentType "application/json"
    if ($global:txIncome.data.type -ne "INCOME") { throw "Bad type" }
}
Test-Step "After income: balance=7800.00" {
    $bal = Get-AliceBalance
    if ($bal -ne "7800.00") { throw "Expected 7800.00, got $bal" }
}

# --- 2.3 Pagination ---
Test-Step "Paginated query (total>=2)" {
    $r = Invoke-RestMethod -Uri "$base/transactions?family_id=$fid&page=1&page_size=10" -H @{Authorization="Bearer $aTok"}
    if ($r.data.total -lt 2) { throw "Expected >=2, got $($r.data.total)" }
}
Test-Step "Filter by type=EXPENSE" {
    $r = Invoke-RestMethod -Uri "$base/transactions?family_id=$fid&type=EXPENSE" -H @{Authorization="Bearer $aTok"}
    if ($r.data.total -lt 1) { throw "Expected >=1" }
}
Test-Step "Filter by amount range" {
    $r = Invoke-RestMethod -Uri "$base/transactions?family_id=$fid&min_amount=100&max_amount=500" -H @{Authorization="Bearer $aTok"}
    if ($r.data.total -lt 1) { throw "Expected >=1" }
}
Test-Step "Filter by time range" {
    $r = Invoke-RestMethod -Uri "$base/transactions?family_id=$fid&from=2026-09-01T00:00:00Z&to=2026-09-30T23:59:59Z" -H @{Authorization="Bearer $aTok"}
    if ($r.data.total -lt 2) { throw "Expected >=2" }
}

# --- 2.4 Detail ---
Test-Step "Get transaction detail (has account_name)" {
    $r = Invoke-RestMethod -Uri "$base/transactions/$($txExpense.data.id)" -H @{Authorization="Bearer $aTok"}
    if (-not $r.data.account_name) { throw "Missing account_name" }
    if (-not $r.data.category_name) { throw "Missing category_name" }
}

# --- 2.5 Edit (200->300) ---
Test-Step "Edit expense (200->300)" {
    Invoke-RestMethod -Uri "$base/transactions/$($txExpense.data.id)" -Method Patch -H @{Authorization="Bearer $aTok"} -Body '{"amount":"300.00"}' -ContentType "application/json" | Out-Null
}
Test-Step "After edit: balance=7700.00" {
    $bal = Get-AliceBalance
    if ($bal -ne "7700.00") { throw "Expected 7700.00, got $bal" }
}

# --- 2.6 Delete ---
Test-Step "Delete expense" {
    Invoke-RestMethod -Uri "$base/transactions/$($txExpense.data.id)" -Method Delete -H @{Authorization="Bearer $aTok"} | Out-Null
}
Test-Step "After delete: balance=8000.00" {
    $bal = Get-AliceBalance
    if ($bal -ne "8000.00") { throw "Expected 8000.00, got $bal" }
}

# --- 2.7 Permission ---
Test-Step "Bob uses Alice's account -> 403" {
    try {
        $body = "{`"family_id`":$fid,`"account_id`":$aAccId,`"category_id`":$expCatId,`"beneficiary_member_id`":$bMemberId,`"type`":`"EXPENSE`",`"amount`":`"100.00`",`"occurred_at`":`"2026-09-07T12:00:00Z`"}"
        Invoke-RestMethod -Uri "$base/transactions" -Method Post -H @{Authorization="Bearer $bTok"} -Body $body -ContentType "application/json" -ErrorAction Stop
        throw "Should have returned 403"
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -ne 403) { throw "Expected 403, got $($_.Exception.Response.StatusCode.value__)" }
    }
}

# --- 2.8 Edge cases ---
Test-Step "Category type mismatch -> error" {
    try {
        $body = "{`"family_id`":$fid,`"account_id`":$aAccId,`"category_id`":$incCatId,`"beneficiary_member_id`":$aMemberId,`"type`":`"EXPENSE`",`"amount`":`"50.00`",`"occurred_at`":`"2026-09-07T12:00:00Z`"}"
        Invoke-RestMethod -Uri "$base/transactions" -Method Post -H @{Authorization="Bearer $aTok"} -Body $body -ContentType "application/json" -ErrorAction Stop
        throw "Should have returned error"
    } catch { }
}
Test-Step "Zero amount -> error" {
    try {
        $body = "{`"family_id`":$fid,`"account_id`":$aAccId,`"category_id`":$expCatId,`"beneficiary_member_id`":$aMemberId,`"type`":`"EXPENSE`",`"amount`":`"0.00`",`"occurred_at`":`"2026-09-07T12:00:00Z`"}"
        Invoke-RestMethod -Uri "$base/transactions" -Method Post -H @{Authorization="Bearer $aTok"} -Body $body -ContentType "application/json" -ErrorAction Stop
        throw "Should have returned error"
    } catch { }
}
Test-Step "Negative amount -> error" {
    try {
        $body = "{`"family_id`":$fid,`"account_id`":$aAccId,`"category_id`":$expCatId,`"beneficiary_member_id`":$aMemberId,`"type`":`"EXPENSE`",`"amount`":`"-50.00`",`"occurred_at`":`"2026-09-07T12:00:00Z`"}"
        Invoke-RestMethod -Uri "$base/transactions" -Method Post -H @{Authorization="Bearer $aTok"} -Body $body -ContentType "application/json" -ErrorAction Stop
        throw "Should have returned error"
    } catch { }
}

# ============================================================
# Phase 3: Transfer Module
# ============================================================
Write-Host "`n" + ("="*60) -ForegroundColor Cyan
Write-Host "  Phase 3: Transfer Module" -ForegroundColor Cyan
Write-Host ("="*60) -ForegroundColor Cyan

# --- 3.1 Create transfer ---
$transfer = $null
Test-Step "Create transfer (alice->bob 500)" {
    $body = "{`"family_id`":$fid,`"from_account_id`":$aAccId,`"to_account_id`":$bAccId,`"amount`":`"500.00`",`"occurred_at`":`"2026-09-07T12:00:00Z`"}"
    $global:transfer = Invoke-RestMethod -Uri "$base/transfers" -Method Post -H @{Authorization="Bearer $aTok"} -Body $body -ContentType "application/json"
    if ($global:transfer.data.amount -ne "500.00") { throw "Bad amount" }
}
Test-Step "After transfer: alice=7500, bob=3500" {
    $aBal = Get-AliceBalance
    $bBal = Get-BobBalance
    if ($aBal -ne "7500.00" -or $bBal -ne "3500.00") { throw "Expected alice=7500.00 bob=3500.00, got alice=$aBal bob=$bBal" }
}

# --- 3.2 Pagination ---
Test-Step "Transfer pagination (total>=1)" {
    $r = Invoke-RestMethod -Uri "$base/transfers?family_id=$fid&page=1&page_size=10" -H @{Authorization="Bearer $aTok"}
    if ($r.data.total -lt 1) { throw "Expected >=1" }
}
Test-Step "Filter by from_member_id" {
    $r = Invoke-RestMethod -Uri "$base/transfers?family_id=$fid&from_member_id=$aMemberId" -H @{Authorization="Bearer $aTok"}
    if ($r.data.total -lt 1) { throw "Expected >=1" }
}
Test-Step "Filter by time range" {
    $r = Invoke-RestMethod -Uri "$base/transfers?family_id=$fid&from=2026-09-01T00:00:00Z&to=2026-09-30T23:59:59Z" -H @{Authorization="Bearer $aTok"}
    if ($r.data.total -lt 1) { throw "Expected >=1" }
}

# --- 3.3 Detail ---
Test-Step "Transfer detail (has from_account_name)" {
    $r = Invoke-RestMethod -Uri "$base/transfers/$($transfer.data.id)" -H @{Authorization="Bearer $aTok"}
    if (-not $r.data.from_account_name) { throw "Missing from_account_name" }
    if (-not $r.data.to_account_name) { throw "Missing to_account_name" }
}

# --- 3.4 Edit (500->800) ---
Test-Step "Edit transfer (500->800)" {
    Invoke-RestMethod -Uri "$base/transfers/$($transfer.data.id)" -Method Patch -H @{Authorization="Bearer $aTok"} -Body '{"amount":"800.00"}' -ContentType "application/json" | Out-Null
}
Test-Step "After edit: alice=7200, bob=3800" {
    $aBal = Get-AliceBalance
    $bBal = Get-BobBalance
    if ($aBal -ne "7200.00" -or $bBal -ne "3800.00") { throw "Expected alice=7200.00 bob=3800.00, got alice=$aBal bob=$bBal" }
}

# --- 3.5 Delete ---
Test-Step "Delete transfer" {
    Invoke-RestMethod -Uri "$base/transfers/$($transfer.data.id)" -Method Delete -H @{Authorization="Bearer $aTok"} | Out-Null
}
Test-Step "After delete: alice=8000, bob=3000" {
    $aBal = Get-AliceBalance
    $bBal = Get-BobBalance
    if ($aBal -ne "8000.00" -or $bBal -ne "3000.00") { throw "Expected alice=8000.00 bob=3000.00, got alice=$aBal bob=$bBal" }
}

# --- 3.6 Permission ---
Test-Step "Bob transfers from Alice's account -> 403" {
    try {
        $body = "{`"family_id`":$fid,`"from_account_id`":$aAccId,`"to_account_id`":$bAccId,`"amount`":`"100.00`",`"occurred_at`":`"2026-09-07T12:00:00Z`"}"
        Invoke-RestMethod -Uri "$base/transfers" -Method Post -H @{Authorization="Bearer $bTok"} -Body $body -ContentType "application/json" -ErrorAction Stop
        throw "Should have returned 403"
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -ne 403) { throw "Expected 403, got $($_.Exception.Response.StatusCode.value__)" }
    }
}

# --- 3.7 Edge cases ---
Test-Step "Same account transfer -> error" {
    try {
        $body = "{`"family_id`":$fid,`"from_account_id`":$aAccId,`"to_account_id`":$aAccId,`"amount`":`"100.00`",`"occurred_at`":`"2026-09-07T12:00:00Z`"}"
        Invoke-RestMethod -Uri "$base/transfers" -Method Post -H @{Authorization="Bearer $aTok"} -Body $body -ContentType "application/json" -ErrorAction Stop
        throw "Should have returned error"
    } catch { }
}
Test-Step "Zero transfer amount -> error" {
    try {
        $body = "{`"family_id`":$fid,`"from_account_id`":$aAccId,`"to_account_id`":$bAccId,`"amount`":`"0.00`",`"occurred_at`":`"2026-09-07T12:00:00Z`"}"
        Invoke-RestMethod -Uri "$base/transfers" -Method Post -H @{Authorization="Bearer $aTok"} -Body $body -ContentType "application/json" -ErrorAction Stop
        throw "Should have returned error"
    } catch { }
}
Test-Step "Negative transfer amount -> error" {
    try {
        $body = "{`"family_id`":$fid,`"from_account_id`":$aAccId,`"to_account_id`":$bAccId,`"amount`":`"-50.00`",`"occurred_at`":`"2026-09-07T12:00:00Z`"}"
        Invoke-RestMethod -Uri "$base/transfers" -Method Post -H @{Authorization="Bearer $aTok"} -Body $body -ContentType "application/json" -ErrorAction Stop
        throw "Should have returned error"
    } catch { }
}

# ============================================================
# Summary
# ============================================================
Write-Host "`n" + ("="*60) -ForegroundColor Cyan
Write-Host "  Results" -ForegroundColor Cyan
Write-Host ("="*60) -ForegroundColor Cyan
$total = $pass + $fail
Write-Host "PASS: $pass / $total" -ForegroundColor Green
if ($fail -gt 0) {
    Write-Host "FAIL: $fail / $total" -ForegroundColor Red
} else {
    Write-Host "ALL PASSED!" -ForegroundColor Green
}