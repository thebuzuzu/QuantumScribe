# Procedimento de release do QuantumScribe

Este é o procedimento operacional para releases disparadas por uma tag `v*`.
O caminho de publicação é deliberadamente separado do caminho de build: nenhum
job de build possui permissão de escrita em Releases.

## Perfis canônicos

- Core CPU: `requirements-core.in` e `requirements-core.lock`.
- Build Windows: `requirements-build.txt` e `requirements-build.lock`.
- Build Linux: `requirements-build-linux.txt` e `requirements-build-linux.lock`.
- Testes/auditoria: `requirements-dev.txt` e `requirements-test.lock`.
- CUDA e Silero VAD: `requirements-cuda-component.txt` e
  `requirements-vad-component.txt`, sempre fora do Core.

Os locks são gerados para Python 3.11, com hashes SHA-256 e faixa de suporte do
projeto `>=3.11,<3.14`. O pipeline instala com `--require-hashes`; não há
instalação aberta no caminho de release.

## Fluxo obrigatório

1. Linux cria o Core em ambiente limpo, com as dependências de sistema do
   workflow, executa `pip check`, PyInstaller, a redução determinística de
   binários de terceiros e o inventário de 250 MB; links simbólicos do bundle
   são inventariados sem duplicar o alvo.
   Então envia os artefatos para o armazenamento interno do workflow.
2. Windows baixa o artefato Linux validado, instala o perfil de testes, roda
   compilação, Ruff, pytest, `pip check` e `pip-audit`, e cria o Core Windows.
3. O Core Windows é reprovado se o inventário encontrar CUDA, Torch, ONNX
   Runtime, VAD neural, modelos ou bibliotecas opcionais proibidas.
4. Componentes CUDA/VAD são gerados em ambiente próprio, recebem
   `component.json` com tamanho e SHA-256 por arquivo e passam pela validação de
   ZIP antes de serem enviados.
5. O job `publish` só começa após os dois builds concluírem com sucesso. Ele
   combina os artefatos validados, publica `SHA256SUMS.txt` e só então torna a
   release pública.

## Evidências mínimas

Cada release deve conter:

- instalador Windows Core;
- pacote Linux Core;
- ZIPs opcionais apenas quando os validadores aprovarem seus manifestos;
- `SHA256SUMS.txt` consolidado;
- inventários produzidos pelos builds.

## Rollback

Não reutilize nem sobrescreva uma release pública validada. Em caso de falha,
mantenha a tag anterior conhecida como boa como referência, remova a publicação
da release incompleta antes de oferecer uma nova tag e corrija o problema em uma
nova execução do workflow. A recuperação não deve alterar, limpar ou reconstruir
o histórico Git local.

## Reprodução local

No Windows, quando `python` não estiver no PATH, passe o interpretador explícito:

```powershell
.\build.ps1 -PythonCommand "C:\\caminho\\python.exe"
```

O build Linux deve ser reproduzido em Ubuntu com Bash e as dependências de sistema
descritas em `.github/workflows/release.yml`. O host de desenvolvimento Windows
não é considerado evidência de build Linux.
