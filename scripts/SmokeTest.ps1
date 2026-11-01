param(
    [Uri] $BaseUri = 'http://localhost:8080'
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Net.Http
$handler = [System.Net.Http.HttpClientHandler]::new()
$handler.AllowAutoRedirect = $false
$client = [System.Net.Http.HttpClient]::new($handler)
$client.BaseAddress = $BaseUri
$client.Timeout = [TimeSpan]::FromSeconds(10)

function Assert-True([bool] $Condition, [string] $Message) {
    if (-not $Condition) { throw $Message }
}

try {
    $response = $client.GetAsync('/health').GetAwaiter().GetResult()
    try {
        $body = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
        Assert-True ([int] $response.StatusCode -eq 200) "GET /health returned $([int] $response.StatusCode); expected 200."
        Assert-True ($body -ceq 'Healthy') "GET /health returned '$body'; expected 'Healthy'."
        Assert-True ($response.Content.Headers.ContentType.MediaType -eq 'text/plain') 'Health response must be plain text.'
        Assert-True ($response.Headers.CacheControl.NoStore) 'Health responses must not be cached.'
        Write-Output 'PASS: /health returns HTTP 200, Healthy, and no-store.'
    }
    finally { $response.Dispose() }

    $response = $client.GetAsync('/').GetAwaiter().GetResult()
    try {
        Assert-True ([int] $response.StatusCode -eq 200) 'GET / must return HTTP 200.'
        Assert-True ($response.Content.Headers.ContentType.MediaType -eq 'application/json') 'Root response must be JSON.'
        $body = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult() | ConvertFrom-Json
        Assert-True ($body.service -ceq 'ubuntu-apps-health-api') 'Root response must identify the service.'
        Assert-True ($body.health -ceq '/health') 'Root response must identify the health endpoint.'
        Write-Output 'PASS: / identifies the service and health endpoint.'
    }
    finally { $response.Dispose() }

    $response = $client.GetAsync('/does-not-exist').GetAwaiter().GetResult()
    try {
        Assert-True ([int] $response.StatusCode -eq 404) 'Unknown routes must return HTTP 404.'
        Write-Output 'PASS: unknown routes return HTTP 404.'
    }
    finally { $response.Dispose() }

    Write-Output 'All 3 HTTP smoke checks passed.'
}
finally {
    $client.Dispose()
}
