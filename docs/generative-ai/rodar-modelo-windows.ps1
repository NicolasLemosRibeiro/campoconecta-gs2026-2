$ErrorActionPreference = 'Stop'
$raiz = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$local = Join-Path $raiz '.assistente-local'
$modelo = Join-Path $local 'qwen2.5-1.5b-instruct-q4_k_m.gguf'
$zip = Join-Path $local 'llama-b6000-bin-win-cpu-x64.zip'
$bin = Join-Path $local 'llama'
New-Item -ItemType Directory -Force $local | Out-Null

function Baixar-Verificado($url, $destino, $sha) {
    if ((Test-Path -LiteralPath $destino -PathType Leaf) -and
        (Get-FileHash -LiteralPath $destino -Algorithm SHA256).Hash -eq $sha) {
        return
    }
    $parcial = "$destino.part"
    curl.exe --fail --location --retry 2 --output $parcial $url
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao baixar $url"
    }
    if ((Get-FileHash -LiteralPath $parcial -Algorithm SHA256).Hash -ne $sha) {
        throw "SHA-256 divergente para $url"
    }
    Move-Item -LiteralPath $parcial -Destination $destino -Force
}

$pacoteUrl = 'https://github.com/ggml-org/llama.cpp/releases/download/b6000/llama-b6000-bin-win-cpu-x64.zip'
$modeloUrl = 'https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/91cad51170dc346986eccefdc2dd33a9da36ead9/qwen2.5-1.5b-instruct-q4_k_m.gguf'
Baixar-Verificado $pacoteUrl $zip 'B32AE2698268562F951C983CAC8333607B9D5B546DE17FD800A02FBC58B06B6D'
Baixar-Verificado $modeloUrl $modelo '6A1A2EB6D15622BF3C96857206351BA97E1AF16C30D7A74EE38970E434E9407E'

$servidor = Join-Path $bin 'llama-server.exe'
if (-not (Test-Path -LiteralPath $servidor -PathType Leaf)) {
    Expand-Archive -LiteralPath $zip -DestinationPath $bin -Force
}
& $servidor --model $modelo --host 127.0.0.1 --port 8088 --ctx-size 2048 --threads 6 --parallel 1
exit $LASTEXITCODE
