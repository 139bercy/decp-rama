pushd "%~dp0"
wsl docker run --rm --pull=always -v $(wslpath -a .):/currentDir -v /var/run/docker.sock:/var/run/docker.sock -v trivy:/root/.cache/ aquasec/trivy image --scanners vuln --format template --template "@contrib/html.tpl" -o /currentDir/trivy.html decp-database
pause